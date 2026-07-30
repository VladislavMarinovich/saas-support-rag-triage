"""Build the feature matrix for the triage classifier.

Each ticket's text (subject + body) is embedded into a 768-dim vector — the SAME
embeddings used for RAG retrieval, now reused as classifier features (one infra,
two uses). The matrix is cached to disk so we embed the 2,038 tickets only once.

Reads the LOCAL dataset (data/tickets.jsonl) — training reads a file, not a
database; Mongo is for the live app later.
"""

from __future__ import annotations

import json
import os

import numpy as np

from src.embed import embed_texts

DATA = "data/tickets_v2.jsonl"
CACHE = "data/ticket_features_v2.npy"


def load_tickets() -> list[dict]:
    with open(DATA, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_features(force: bool = False):
    """Return (X, tickets): X is a (n, 768) float32 matrix aligned to tickets."""
    tickets = load_tickets()
    # reuse the cached matrix if present — embedding 2,038 tickets costs time/money
    if os.path.exists(CACHE) and not force:
        X = np.load(CACHE)
        assert X.shape[0] == len(tickets), "cache stale — rerun with force=True"
        return X, tickets

    # feature = each ticket's subject+body embedded; save so we embed only once
    texts = [f"{t['subject']}\n{t['body']}".strip() for t in tickets]
    X = np.asarray(embed_texts(texts), dtype="float32")
    np.save(CACHE, X)
    return X, tickets


if __name__ == "__main__":
    X, tickets = build_features()
    print(f"feature matrix: {X.shape}  ({X.shape[0]} tickets × {X.shape[1]} dims)")
    print(f"cached to {CACHE}")
