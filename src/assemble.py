"""Assemble the per-month ticket files into the final dataset.

Concatenates data/2026-*.jsonl, sorts by created_at, and renumbers ticket_id
globally (TCK-000001 = the earliest ticket of the whole year) so IDs are
monotonic with time across the entire dataset. Output: data/tickets.jsonl.

Run:  uv run python -m src.assemble
"""

from __future__ import annotations

import glob
import json
from pathlib import Path


def assemble(pattern: str = "data/2026-*.jsonl", out: str = "data/tickets.jsonl"):
    """Merge monthly files → chronological, globally-renumbered dataset."""
    files = sorted(glob.glob(pattern))
    rows: list[dict] = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            rows.extend(json.loads(line) for line in fh)

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
