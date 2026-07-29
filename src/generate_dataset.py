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
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.prompts import build_prompt
from src.generate_tickets import _parse_llm_json, _print_preview
from src.generate_event_layer import generate_plan, FEATURE_REQUEST_SCENARIO


def _in_quarter(created_at: str, year: int, q: int) -> bool:
    """True if an ISO created_at falls in the given calendar quarter."""
    yr, mo = int(created_at[:4]), int(created_at[5:7])
    return yr == year and (q - 1) * 3 < mo <= q * 3


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


def _generate_one(spec, max_retries: int = 6):
    """Worker: spec -> LLM -> ('ok', rec) or ('skip', (id, error)).

    Retries with exponential backoff + jitter (2->4->8->16->30s). This rides out
    Vertex 429 RESOURCE_EXHAUSTED windows: when a thread hits the quota it sleeps
    and retries instead of dropping the ticket, which also self-throttles the pool.
    """
    from src.llm import generate  # lazy import so --dry needs no credentials
    delay = 2.0
    for attempt in range(max_retries):
        try:
            raw = generate(build_prompt(spec), max_tokens=512)
            subject, body = _parse_llm_json(raw)
            rec = spec.to_record()
            rec["subject"], rec["body"] = subject, body
            return "ok", rec
        except Exception as e:
            if attempt == max_retries - 1:
                return "skip", (spec.ticket_id, str(e)[:120])
            time.sleep(delay + random.random())  # jitter avoids thundering herd
            delay = min(delay * 2, 30.0)


def run(specs: list, out: Path | None, *, dry: bool, preview: bool,
        workers: int = 5) -> None:
    if dry:
        for spec in specs:
            print("─" * 72)
            print(f"{spec.ticket_id}  scenario={spec.scenario_id}  "
                  f"event={spec.event_id}")
            print(build_prompt(spec))
        return

    # skip ticket_ids already written (resume a long / batched run)
    done = _done_ids(out) if out else set()
    todo = [s for s in specs if s.ticket_id not in done]
    if done:
        print(f"resuming: {len(done)} already in {out}, {len(todo)} to go")

    lock = threading.Lock()  # serialize the incremental writes across threads
    f = out.open("a", encoding="utf-8") if out else None
    written = skipped = 0
    try:
        # API calls are I/O-bound -> threads give near-linear speedup. Results are
        # written as they complete (order-independent; ids are already assigned).
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_generate_one, s) for s in todo]
            for fut in as_completed(futures):
                status, payload = fut.result()
                if status == "skip":
                    tid, err = payload
                    print(f"skip {tid}: {err}")
                    skipped += 1
                    continue
                with lock:
                    if f:
                        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
                        f.flush()  # crash-safe: each ticket hits disk immediately
                    written += 1
                    if preview and written <= 5:
                        _print_preview(payload)
                    elif written % 100 == 0:
                        print(f"  ... {written} generated")
    finally:
        if f:
            f.close()
    print("─" * 72)
    print(f"generated {written} tickets ({skipped} skipped)"
          + (f" -> {out}" if out else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="generate a small representative slice (launches, outage, base)")
    ap.add_argument("--quarter", type=str, default=None,
                    help="restrict to a calendar quarter, format YYYY-Qn (e.g. 2024-Q1)")
    ap.add_argument("--limit", type=int, default=None, help="cap number of specs")
    ap.add_argument("--out", type=str, default=None, help="JSONL output path (append/resume)")
    ap.add_argument("--dry", action="store_true", help="print prompts only, no LLM call")
    ap.add_argument("--seed", type=int, default=11, help="plan seed (reproducible)")
    ap.add_argument("--workers", type=int, default=5, help="concurrent LLM calls")
    args = ap.parse_args()

    plan = generate_plan(seed=args.seed)
    print(f"plan: {len(plan)} specs")

    if args.smoke:
        specs = smoke_specs(plan)
    else:
        specs = plan
        if args.quarter:
            year, q = args.quarter.upper().split("-Q")
            specs = [s for s in specs if _in_quarter(s.created_at, int(year), int(q))]
            print(f"quarter {args.quarter}: {len(specs)} specs")
        if args.limit:
            specs = specs[:args.limit]

    out = Path(args.out) if args.out else None
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
    # preview a few only for small runs (smoke); stay quiet for the bulk
    run(specs, out, dry=args.dry, preview=args.smoke, workers=args.workers)


if __name__ == "__main__":
    main()
