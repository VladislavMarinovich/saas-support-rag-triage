"""
Ticket generator: sample specs -> prompt -> LLM -> subject/body -> record.

Usage:
  python -m src.generate_tickets --n 1                 # generate + print
  python -m src.generate_tickets --n 20 --out data/tickets.jsonl
  python -m src.generate_tickets --n 1 --dry           # print the prompt only ($0)

`--dry` builds the prompt and prints it WITHOUT calling the LLM — use it to
inspect prompts for free before spending anything.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.sampler import sample_batch, sample_month
from src.prompts import build_prompt


def _parse_llm_json(text: str) -> tuple[str, str]:
    """Extract subject/body from the model's reply, tolerating markdown fences."""
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in reply: {text[:200]!r}")
    obj = json.loads(text[start:end + 1])
    return obj.get("subject", ""), obj.get("body", "")


def _print_preview(rec: dict) -> None:
    print("─" * 72)
    print(f"{rec['ticket_id']}  [{rec['created_at']}]  {rec['channel']} · "
          f"{rec['plan']} · {rec['user_role']}")
    print(f"labels: topic={rec['topic']} type={rec['type']} "
          f"priority={rec['priority']} routing={rec['routing']} "
          f"sentiment={rec['sentiment']}")
    print(f"reported_category (intake, noisy): {rec['reported_category']}")
    print(f"SUBJECT: {rec.get('subject', '')!r}")
    print(f"BODY:\n{rec.get('body', '')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1, help="how many tickets")
    ap.add_argument("--seed", type=int, default=7, help="sampler seed (reproducible)")
    ap.add_argument("--month", type=str, default=None,
                    help="restrict created_at to a month, format YYYY-MM (e.g. 2026-01)")
    ap.add_argument("--out", type=str, default=None, help="JSONL output path")
    ap.add_argument("--dry", action="store_true", help="print prompts only, no LLM call")
    args = ap.parse_args()

    if args.month:
        year, month = (int(x) for x in args.month.split("-"))
        specs = sample_month(year, month, args.n, seed=args.seed)
    else:
        specs = sample_batch(args.n, seed=args.seed)

    if args.dry:
        for spec in specs:
            print("─" * 72)
            print(f"{spec.ticket_id}  scenario={spec.scenario_id}")
            print(build_prompt(spec))
        return

    # Import the LLM client only when we actually generate (so --dry needs no key).
    from src.llm import generate

    records = []
    for spec in specs:
        # One retry, then skip — a single bad JSON reply must not abort a big run.
        for attempt in range(2):
            try:
                raw = generate(build_prompt(spec), max_tokens=512)
                subject, body = _parse_llm_json(raw)
                break
            except Exception as e:
                if attempt == 1:
                    print(f"skip {spec.ticket_id}: {e}")
                    subject = body = None
        if body is None:
            continue
        rec = spec.to_record()
        rec["subject"] = subject
        rec["body"] = body
        records.append(rec)
        _print_preview(rec)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print("─" * 72)
        print(f"wrote {len(records)} tickets -> {out}")


if __name__ == "__main__":
    main()
