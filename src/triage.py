"""Unified triage pipeline — the front door that ties the two pillars together.

    ticket text ->  classify (5 labels)  ->  gate on routing:
                        kb_autoresolve  -> answer from the KB (RAG)
                        anything else   -> escalate to the right team

This is what turns "two scripts" (classifier + RAG) into one system.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

from src.embed import embed_texts
from src.features import build_features
from src.rag import answer as rag_answer

LABELS = ["topic", "type", "priority", "routing", "sentiment"]

_models: dict | None = None


def get_models() -> dict:
    """Train one classifier per label on ALL tickets (lazy, cached in memory).

    We train on the full dataset here (not an 80/20 split) because this is the
    deployable predictor, not the evaluation — accuracy was measured in classify.py.
    """
    global _models
    if _models is None:
        # features = the cached ticket embeddings; train one model per label
        X, tickets = build_features()
        _models = {}
        for label in LABELS:
            y = np.array([t[label] for t in tickets])
            clf = LogisticRegression(max_iter=1000, class_weight="balanced")
            clf.fit(X, y)
            _models[label] = clf
    return _models


def predict(text: str) -> dict:
    """Predict the 5 triage labels for a new ticket from its text."""
    # turn the ticket into its embedding, then run each label's classifier on it
    vec = np.asarray(embed_texts([text]), dtype="float32")
    models = get_models()
    return {label: str(models[label].predict(vec)[0]) for label in LABELS}


def triage(text: str) -> dict:
    """Classify the ticket, then answer from the KB or escalate."""
    labels = predict(text)
    # gate on the predicted routing: KB-deflectable -> RAG answers; else escalate
    if labels["routing"] == "kb_autoresolve":
        reply, _hits = rag_answer(text)
        action = "answered_from_kb"
    else:
        action = "escalated"
        reply = (f"Escalated to {labels['routing']} (priority: {labels['priority']}). "
                 f"A specialist will follow up.")
    return {"labels": labels, "action": action, "response": reply}


if __name__ == "__main__":
    examples = [
        "how do I connect my hubspot account?",                              # -> kb
        "our entire dashboard is down and we can't see any metrics, this is urgent!",  # -> escalate (incident)
        "we'd like to upgrade to the enterprise plan, who do I talk to?",    # -> escalate (sales)
    ]
    for t in examples:
        r = triage(t)
        print("=" * 72)
        print(f"TICKET:   {t}")
        print(f"LABELS:   {r['labels']}")
        print(f"ACTION:   {r['action']}")
        print(f"RESPONSE: {r['response'][:280].strip()}")
        print()
