"""
Dataset runner: take the event-layer PLAN -> LLM -> write the tickets JSONL.

Consumes src.generate_event_layer.generate_plan() (base flow + event layer) and
generates the customer text for each spec via src.prompts.build_prompt + the LLM.

Writes INCREMENTALLY (one JSON line per ticket, flushed) so a long background run
is crash-safe and RESUMABLE: re-running with the same --out skips ticket_ids
already present in the file and continues where it left off.

Usage:
  python -m src.generate_dataset --smoke --dry           # inspect ~8 prompts, $0
  python -m src.generate_dataset --smoke --out data/smoke.jsonl   # ~8-ticket test
  python -m src.generate_dataset --out data/tickets_v2.jsonl      # full ~24k (resumable)

Provider follows LLM_PROVIDER (anthropic|vertex); use vertex for the cheap bulk.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.prompts import build_prompt
from src.generate_tickets import _parse_llm_json, _print_preview
from src.generate_event_layer import generate_plan, FEATURE_REQUEST_SCENARIO


def smoke_specs(plan: list) -> list:
    """A small, REPRESENTATIVE slice: launches (with feature), an outage, base.

    Picking the first N specs would only give January-2024 base tickets — useless
    for verifying the event flavors. This hand-picks coverage instead.
    """
    picks: list = []
    seen_launch: set = set()
    # two launch how-to tickets from two DIFFERENT launches (distinct features)
    for s in plan:
        if (s.event_type == "launch" and s.scenario_id != FEATURE_REQUEST_SCENARIO
                and s.event_id not in seen_launch):
            picks.append(s)
            seen_launch.add(s.event_id)
            if len(seen_launch) == 2:
                break
    # one pre-launch feature-request ("when will you add connector X?")
    picks += [next(s for s in plan if s.scenario_id == FEATURE_REQUEST_SCENARIO)]
    # two outage tickets (error reports) and three base-flow tickets
    picks += [s for s in plan if s.event_type == "outage"][:2]
    picks += [s for s in plan if s.event_id is None][:3]
    return picks


def _done_ids(out: Path) -> set:
    """ticket_ids already written to `out` (for resuming a long run)."""
    if not out.exists():
        return set()
    done = set()
    with out.open(encoding="utf-8") as f:
        for line in f:
            try:
                done.add(json.loads(line)["ticket_id"])
            except Exception:
                pass
    return done


def run(specs: list, out: Path | None, *, dry: bool, preview: bool) -> None:
    if dry:
        for spec in specs:
            print("─" * 72)
            print(f"{spec.ticket_id}  scenario={spec.scenario_id}  "
                  f"event={spec.event_id}")
            print(build_prompt(spec))
        return

    from src.llm import generate  # imported lazily so --dry needs no credentials

    done = _done_ids(out) if out else set()
    if done:
        print(f"resuming: {len(done)} tickets already in {out}, skipping those")
    f = out.open("a", encoding="utf-8") if out else None
    written = 0
    try:
        for spec in specs:
            if spec.ticket_id in done:
                continue
            # one retry, then skip — a single bad reply must not abort a big run
            subject = body = None
            for attempt in range(2):
                try:
                    raw = generate(build_prompt(spec), max_tokens=512)
                    subject, body = _parse_llm_json(raw)
                    break
                except Exception as e:
                    if attempt == 1:
                        print(f"skip {spec.ticket_id}: {e}")
            if body is None:
                continue
            rec = spec.to_record()
            rec["subject"], rec["body"] = subject, body
            if f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()  # crash-safe: each ticket hits disk immediately
            written += 1
            if preview:
                _print_preview(rec)
            elif written % 100 == 0:
                print(f"  ... {written} generated")
    finally:
        if f:
            f.close()
    print("─" * 72)
    print(f"generated {written} tickets" + (f" -> {out}" if out else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="generate a small representative slice (launches, outage, base)")
    ap.add_argument("--limit", type=int, default=None, help="cap number of specs")
    ap.add_argument("--out", type=str, default=None, help="JSONL output path (append/resume)")
    ap.add_argument("--dry", action="store_true", help="print prompts only, no LLM call")
    ap.add_argument("--seed", type=int, default=11, help="plan seed (reproducible)")
    args = ap.parse_args()

    plan = generate_plan(seed=args.seed)
    print(f"plan: {len(plan)} specs")

    if args.smoke:
        specs = smoke_specs(plan)
    elif args.limit:
        specs = plan[:args.limit]
    else:
        specs = plan

    out = Path(args.out) if args.out else None
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
    # preview each ticket only for small runs (smoke / dry); stay quiet for the bulk
    run(specs, out, dry=args.dry, preview=args.smoke or bool(args.limit))


if __name__ == "__main__":
    main()
