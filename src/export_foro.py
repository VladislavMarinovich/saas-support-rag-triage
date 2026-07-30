"""Exporta de Mongo los tickets ya respondidos → JSON estático para el foro (UI).

El foro de Cloudflare Pages es estático: no consulta Mongo en runtime, lee este
JSON curado (build-time export). Mongo sigue siendo el system-of-record; esto es
sólo una foto para servir rápido. Sólo salen tickets que YA tienen respuesta.

Run:  python -m src.export_foro                 # -> web/data/tickets.json
      python -m src.export_foro --limit 500     # cap distinto
"""

from __future__ import annotations

import argparse
import json
import os

from src.mongo_store import get_db

OUT = "web/data/tickets.json"

# Campos que el foro muestra (dejamos fuera lo interno). Orden = intención de UI.
FIELDS = [
    "ticket_id", "created_at", "channel", "plan", "user_role", "reported_category",
    "topic", "type", "priority", "routing", "sentiment", "event_id", "event_type",
    "subject", "body", "response", "response_kind",
]


def export(out: str = OUT, limit: int = 500) -> int:
    """Vuelca los tickets con respuesta a un JSON (curado, ordenado por fecha)."""
    db = get_db()
    cursor = (
        db.tickets.find({"response": {"$exists": True}}, {f: 1 for f in FIELDS} | {"_id": 0})
        .sort("created_at", 1)
        .limit(limit)
    )
    docs = [{f: d.get(f) for f in FIELDS} for d in cursor]

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(docs, fh, ensure_ascii=False, indent=1)
    return len(docs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--limit", type=int, default=500)
    args = ap.parse_args()
    n = export(args.out, args.limit)
    print(f"exportados {n} tickets con respuesta → {args.out}")


if __name__ == "__main__":
    main()
