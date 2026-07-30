"""MongoDB store — the system-of-record for the Polaris demo app (the foro UI).

Reads MONGODB_URI from the environment (.env). Database: `polaris`. The `tickets`
collection holds each ticket keyed by `ticket_id`; the app later enriches each doc
with its triage + response and the UI reads from here.

Run:  python -m src.mongo_store            # load tickets into Mongo
      python -m src.mongo_store --ping     # test the connection only
"""

from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv

load_dotenv()

DB_NAME = "polaris"
TICKETS = "data/tickets_v2.jsonl"


def get_db():
    """Return the `polaris` database (raises clearly if the URI is missing)."""
    from pymongo import MongoClient

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise SystemExit("MONGODB_URI not set — add it to .env")
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")  # fail fast if unreachable / bad creds
    return client[DB_NAME]


def load_tickets(path: str = TICKETS) -> int:
    """Upsert every ticket into `tickets` (idempotent — safe to re-run)."""
    from pymongo import ReplaceOne

    db = get_db()
    col = db.tickets
    col.create_index("ticket_id", unique=True)
    col.create_index("created_at")  # the UI browses/sorts by time

    docs = [json.loads(line) for line in open(path, encoding="utf-8")]
    ops = [ReplaceOne({"ticket_id": d["ticket_id"]}, d, upsert=True) for d in docs]
    for i in range(0, len(ops), 1000):  # bulk in chunks
        col.bulk_write(ops[i:i + 1000], ordered=False)
    return col.count_documents({})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ping", action="store_true", help="test the connection only")
    args = ap.parse_args()

    if args.ping:
        db = get_db()
        print("connected OK — collections:", db.list_collection_names())
        return

    n = load_tickets()
    print(f"tickets in Mongo (`{DB_NAME}.tickets`): {n:,}")


if __name__ == "__main__":
    main()
