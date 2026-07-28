"""
Ticket-spec sampler for the synthetic Polaris dataset.

Given the scenario catalog (src/taxonomy.py), this builds the full ticket
*record minus the free text* — i.e. every label + metadata field, plus the
`seed` the prompt builder (next step) needs. No LLM here.

Sampling is REPRODUCIBLE: everything is driven by a seeded random.Random, so the
same (seed, n) always yields the same dataset — a requirement for a pipeline you
can re-run and audit.

Pipeline per ticket (docs/dataset-spec.md §4):
  scenario (by weight) -> sentiment -> plan/channel/role -> created_at
  -> reported_category (noisy) -> length band.

Run `python -m src.sampler` to sample a batch and verify the marginals reproduce
the catalog (priority 60/30/9/1) plus print one example spec.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, asdict, replace
from datetime import datetime, timedelta

from src.taxonomy import (
    SCENARIOS, Scenario,
    TOPICS, TYPES, PRIORITIES, ROUTINGS, SENTIMENTS, REPORTED_CATEGORIES,
    PLAN_WEIGHTS, CHANNEL_WEIGHTS, ROLE_WEIGHTS,
    REPORTED_CATEGORY_NOISE,
)

# Length band per channel — chat skews short, email skews medium/long (§2).
LENGTH_BY_CHANNEL = {
    "chat": {"short": 0.60, "medium": 0.35, "long": 0.05},
    "email": {"short": 0.15, "medium": 0.55, "long": 0.30},
    "in_app": {"short": 0.35, "medium": 0.50, "long": 0.15},
}


@dataclass(frozen=True)
class TicketSpec:
    """A fully-specified ticket, ready for the prompt builder — text excluded."""
    # meta
    ticket_id: str
    created_at: str            # ISO 8601
    # inputs · intake
    channel: str
    plan: str
    user_role: str
    reported_category: str     # NOISY user picklist (may disagree with topic/type)
    # targets (ground truth)
    topic: str
    type: str
    priority: str
    routing: str
    sentiment: str
    # generation hints (not part of the ML task, used only to write the text)
    length_band: str
    scenario_id: str
    seed_text: str
    # reserved for the v2 event layer — always None in v1
    event_id: str | None = None
    event_type: str | None = None

    def to_record(self) -> dict:
        """Dict form for JSONL output (drops the internal generation hints)."""
        d = asdict(self)
        for internal in ("length_band", "scenario_id", "seed_text"):
            d.pop(internal)
        return d


def _weighted_choice(rng: random.Random, mapping: dict[str, float]) -> str:
    """Pick one key from {key: weight}. Weights need not sum to 1."""
    keys = list(mapping)
    return rng.choices(keys, weights=[mapping[k] for k in keys], k=1)[0]


def aligned_category(topic: str, type_: str) -> str:
    """The picklist bucket a *correctly self-tagging* user would pick.

    Type wins over area when the user thinks in terms of what went wrong
    (a bug, a security worry, a how-to); otherwise it maps by feature area.
    """
    if type_ == "how_to":
        return "how_to_question"
    if type_ == "security":
        return "security_concern"
    if type_ in ("bug", "outage"):
        return "bug_something_broken"
    if topic == "billing" or type_ == "billing":
        return "account_billing"
    if topic == "connectors":
        return "connectors_integrations"
    if topic in ("dashboards", "reports", "northstar"):
        return "dashboards_reports"
    if topic == "attribution":
        return "attribution"
    if topic == "alerts":
        return "alerts"
    if topic == "users_workspace":
        return "users_access"
    return "other"


def _reported_category(rng: random.Random, topic: str, type_: str) -> str:
    """Apply the intake-noise model (§4.6): aligned / wrong bucket / other."""
    mode = _weighted_choice(rng, REPORTED_CATEGORY_NOISE)
    if mode == "other":
        return "other"
    aligned = aligned_category(topic, type_)
    if mode == "aligned":
        return aligned
    # wrong bucket: any real category that is neither the aligned one nor 'other'
    choices = [c for c in REPORTED_CATEGORIES if c not in (aligned, "other")]
    return rng.choice(choices)


def _pick_sentiment(rng: random.Random, scenario: Scenario) -> str:
    """Pick from the scenario's fitting sentiments, biased to the first listed
    (its dominant emotion)."""
    n = len(scenario.sentiments)
    weights = [n - i for i in range(n)]  # 3,2,1... -> first is most likely
    return rng.choices(scenario.sentiments, weights=weights, k=1)[0]


def _pick_role(rng: random.Random, scenario: Scenario) -> str:
    """Respect a scenario's role restriction (e.g. 'can't reconnect' needs a
    non-admin); otherwise sample from the global role mix."""
    if scenario.roles:
        keys = list(scenario.roles)
        return rng.choices(keys, weights=[ROLE_WEIGHTS[k] for k in keys], k=1)[0]
    return _weighted_choice(rng, ROLE_WEIGHTS)


def sample_spec(
    rng: random.Random,
    window_start: datetime,
    window_days: int,
) -> TicketSpec:
    """Build one TicketSpec. ticket_id is assigned later (chronologically)."""
    scenario = rng.choices(SCENARIOS, weights=[s.weight for s in SCENARIOS], k=1)[0]

    channel = _weighted_choice(rng, CHANNEL_WEIGHTS)
    plan = _weighted_choice(rng, PLAN_WEIGHTS)
    role = _pick_role(rng, scenario)
    sentiment = _pick_sentiment(rng, scenario)
    length_band = _weighted_choice(rng, LENGTH_BY_CHANNEL[channel])
    reported = _reported_category(rng, scenario.topic, scenario.type)

    # created_at spread uniformly across the window (seeded -> reproducible)
    offset = timedelta(seconds=rng.random() * window_days * 86_400)
    created_at = (window_start + offset).isoformat(timespec="seconds")

    return TicketSpec(
        ticket_id="",  # assigned in sample_batch after sorting by created_at
        created_at=created_at,
        channel=channel,
        plan=plan,
        user_role=role,
        reported_category=reported,
        topic=scenario.topic,
        type=scenario.type,
        priority=scenario.priority,
        routing=scenario.routing,
        sentiment=sentiment,
        length_band=length_band,
        scenario_id=scenario.id,
        seed_text=scenario.seed,
    )


def sample_batch(
    n: int,
    *,
    seed: int = 7,
    window_start: datetime = datetime(2026, 1, 1),
    window_days: int = 180,
) -> list[TicketSpec]:
    """Sample `n` reproducible ticket specs."""
    rng = random.Random(seed)
    specs = [sample_spec(rng, window_start, window_days) for _ in range(n)]
    # Assign ticket_id in chronological order so IDs are monotonic with time,
    # like a real ticketing system (TCK-000001 = the earliest ticket). ISO 8601
    # strings sort chronologically, so a plain string sort is correct.
    specs.sort(key=lambda s: s.created_at)
    return [replace(s, ticket_id=f"TCK-{i + 1:06d}") for i, s in enumerate(specs)]


def validate_catalog() -> None:
    """Fail loudly if any scenario carries a label outside the enums."""
    for s in SCENARIOS:
        assert s.topic in TOPICS, f"{s.id}: bad topic {s.topic}"
        assert s.type in TYPES, f"{s.id}: bad type {s.type}"
        assert s.priority in PRIORITIES, f"{s.id}: bad priority {s.priority}"
        assert s.routing in ROUTINGS, f"{s.id}: bad routing {s.routing}"
        assert set(s.sentiments) <= set(SENTIMENTS), f"{s.id}: bad sentiment"
        assert s.sentiments, f"{s.id}: needs at least one sentiment"


if __name__ == "__main__":
    validate_catalog()

    N = 3000
    batch = sample_batch(N)

    def marginal(field: str):
        acc: dict[str, int] = {}
        for spec in batch:
            v = getattr(spec, field)
            acc[v] = acc.get(v, 0) + 1
        return sorted(((k, c / N) for k, c in acc.items()), key=lambda kv: -kv[1])

    print(f"sampled {N} specs (seed=7)\n")
    for field in ("priority", "routing", "sentiment", "reported_category",
                  "channel", "plan", "user_role"):
        print(field)
        for label, share in marginal(field):
            print(f"  {label:<22} {share * 100:5.1f}%")
        print()

    # intake-noise sanity: how often does the picklist disagree with the truth?
    wrong = sum(
        1 for s in batch
        if s.reported_category != aligned_category(s.topic, s.type)
    )
    print(f"intake mismatch vs truth: {wrong / N * 100:.1f}%  (target ~35%)\n")

    import json
    print("example record:")
    print(json.dumps(batch[0].to_record(), indent=2))
