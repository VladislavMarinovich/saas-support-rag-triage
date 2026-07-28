"""Triage classifier: predict each ticket label from its embedding.

Trains one logistic-regression model per label on 80% of the tickets and
evaluates on the held-out 20% (tickets it never saw) — an honest measure of
whether it learned the pattern vs memorized.

`class_weight='balanced'` so rare classes (e.g. priority=critical ~1%) aren't
ignored; macro-F1 reports per-class performance, not just overall accuracy.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from src.features import build_features

LABELS = ["topic", "type", "priority", "routing", "sentiment"]


def main() -> None:
    X, tickets = build_features()

    print(f"{'label':<12}{'accuracy':>10}{'macro-F1':>10}")
    print("-" * 32)
    results = {}
    for label in LABELS:
        y = np.array([t[label] for t in tickets])
        # hold out 20% the model never sees (stratified to keep rare classes in both)
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=0.2, random_state=7, stratify=y
        )
        # train on the 80%, then predict on the unseen 20%
        clf = LogisticRegression(max_iter=1000, class_weight="balanced")
        clf.fit(X_tr, y_tr)
        pred = clf.predict(X_te)
        # accuracy = overall correct; macro-F1 = per-class (honest with imbalance)
        acc = accuracy_score(y_te, pred)
        f1 = f1_score(y_te, pred, average="macro")
        results[label] = acc
        print(f"{label:<12}{acc:>10.3f}{f1:>10.3f}")

    # Value experiment: the model vs trusting the customer's own picklist.
    from src.sampler import aligned_category
    picklist_right = np.mean([
        t["reported_category"] == aligned_category(t["topic"], t["type"])
        for t in tickets
    ])
    print("\n--- value check (topic) ---")
    print(f"trusting the user's picklist is right ~{picklist_right:.0%} of the time")
    print(f"the model predicts the true topic at {results['topic']:.0%} accuracy")


if __name__ == "__main__":
    main()
