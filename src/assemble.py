"""Assemble the per-month ticket files into the final dataset.

Concatenates the monthly files, assigns each ticket a final `created_at`, sorts
chronologically, and renumbers ticket_id globally (TCK-000001 = earliest).

Why dates are (re)assigned HERE and not during generation: the ticket TEXT is
date-independent — the date is never fed to the LLM — so the final temporal
layout is a pure-local concern. This lets us set a realistic historical window
(ending at the last complete month, no future dates) WITHOUT regenerating any
text, i.e. no LLM cost. Seeded → reproducible.

Run:  uv run python -m src.assemble
"""

from __future__ import annotations

import glob
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Baseline window: a single full PAST year (2024) — no future-dated tickets.
# The richer multi-year growth dataset (2025 at 2–3x volume, "the company grew")
# is generated separately for the Hugging Face release; pass a wider window +
# more data there. Here we just re-date the existing tickets into 2024.
WINDOW_START = datetime(2024, 1, 1)
WINDOW_END = datetime(2025, 1, 1)  # exclusive → last date is 2024-12-31


def assemble(
    pattern: str = "data/20[0-9][0-9]-[0-9][0-9].jsonl",
    out: str = "data/tickets.jsonl",
    window_start: datetime = WINDOW_START,
    window_end: datetime = WINDOW_END,
    seed: int = 7,
):
    """Merge monthly files → re-dated, chronological, globally-renumbered dataset."""
    files = sorted(glob.glob(pattern))
    rows: list[dict] = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh)

    # Reassign created_at uniformly across the historical window (local, no AI).
    rng = random.Random(seed)
    span_seconds = int((window_end - window_start).total_seconds())
    for r in rows:
        offset = timedelta(seconds=rng.randrange(span_seconds))
        r["created_at"] = (window_start + offset).isoformat(timespec="seconds")

    # ISO 8601 strings sort chronologically as plain strings.
    rows.sort(key=lambda r: r["created_at"])
    for i, r in enumerate(rows, start=1):
        r["ticket_id"] = f"TCK-{i:06d}"

    out_path = Path(out)
    with out_path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows, files, out_path


if __name__ == "__main__":
    rows, files, out_path = assemble()
    print(f"assembled {len(rows)} tickets from {len(files)} monthly files -> {out_path}")
    print(f"date range: {rows[0]['created_at']}  ..  {rows[-1]['created_at']}")
    print(f"ids:        {rows[0]['ticket_id']}  ..  {rows[-1]['ticket_id']}")
    years = sorted({r["created_at"][:4] for r in rows})
    print(f"years present: {years}")
