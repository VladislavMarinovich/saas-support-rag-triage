"""
Event-layer generator — builds the full ticket PLAN for the ~24k dataset.

Two layers, additive (see docs/event-layer-spec.md):
  - BASE flow: the steady background, month by month, growing by year
    (2024 -> 2025 ~2x -> 2026 H1). Reuses src.sampler.sample_month unchanged.
  - EVENT layer: on top, each event in src.events injects its extra tickets
    inside its window, biased to its own scenarios and tagged with event_id.

No LLM here: this produces TicketSpecs (labels + metadata + seed_text), i.e. the
temporal PLAN. Generating the actual ticket text on an LLM is a separate step,
run only once this plan's shape is verified against acceptance criteria §6.

Curves (event-layer-spec.md §3):
  - outage : sharp spike — ~80% of the extra tickets in the first 2 days, a short
    tail after. Error-report scenarios ("sync broken", "sync delay").
  - launch : gradual wave — 60/25/15 of the how-to tickets over 3 months, PLUS a
    pre-launch ramp of feature-requests ("when will you add connector X?") that
    falls to ~0 the day the connector ships.

The `feature` name (Salesforce, Zoho...) is injected via the ticket's seed_text,
so no change to the sampler or the prompt builder is needed.

Run `python -m src.generate_event_layer` for the no-LLM dry-run: it prints the
monthly volume (base vs event) and the pre/post-launch feature-request signal.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import replace
from datetime import datetime, timedelta

from src.taxonomy import SCENARIOS, CHANNEL_WEIGHTS, PLAN_WEIGHTS
from src.sampler import (
    TicketSpec, sample_month, LENGTH_BY_CHANNEL,
    _weighted_choice, _pick_sentiment, _pick_role, _reported_category,
)
from src.events import EVENTS

# Span of the dataset: Jan 2024 through Jun 2026 (end is exclusive).
SPAN_START = datetime(2024, 1, 1)
SPAN_END = datetime(2026, 7, 1)

# Base-flow volume per year (the ~75% that is NOT event-driven). 2026 is H1 only.
# Grows over time; events (~6k) land on top for ~24k total.
BASE_PER_YEAR = {2024: 4500, 2025: 8500, 2026: 5000}

# Scenario lookup + the canonical "wants a connector that doesn't exist" scenario
# used for the pre-launch feature-request ramp.
SCEN_BY_ID = {s.id: s for s in SCENARIOS}
FEATURE_REQUEST_SCENARIO = "connectors_feature_request_source"

# Of a launch's magnitude, this share is the pre-launch feature-request ramp; the
# rest is the post-launch how-to wave.
PRELAUNCH_SHARE = 0.25
# How the how-to wave decays across its 3 months.
WAVE_MONTH_SPLIT = (0.60, 0.25, 0.15)


def _build_spec(rng, scenario, created_at, *, seed_text=None,
                event_id=None, event_type=None) -> TicketSpec:
    """Assemble one TicketSpec for a chosen scenario at a chosen time.

    Reuses the sampler's surface sampling (channel/plan/role/sentiment/length/
    intake-noise) so event tickets look exactly like base tickets — only the
    scenario mix and the event tags differ.
    """
    channel = _weighted_choice(rng, CHANNEL_WEIGHTS)
    plan = _weighted_choice(rng, PLAN_WEIGHTS)
    role = _pick_role(rng, scenario)
    sentiment = _pick_sentiment(rng, scenario)
    length_band = _weighted_choice(rng, LENGTH_BY_CHANNEL[channel])
    reported = _reported_category(rng, scenario.topic, scenario.type)
    return TicketSpec(
        ticket_id="",  # assigned globally after sorting by created_at
        created_at=created_at.isoformat(timespec="seconds"),
        channel=channel, plan=plan, user_role=role, reported_category=reported,
        topic=scenario.topic, type=scenario.type, priority=scenario.priority,
        routing=scenario.routing, sentiment=sentiment,
        length_band=length_band, scenario_id=scenario.id,
        seed_text=seed_text or scenario.seed,
        event_id=event_id, event_type=event_type,
    )


def _base_specs(seed: int = 11) -> list[TicketSpec]:
    """The background flow: sample each month across the span, scaled by year."""
    specs: list[TicketSpec] = []
    for year, total in BASE_PER_YEAR.items():
        months = range(1, 7) if year == 2026 else range(1, 13)
        per_month = total // len(list(months))
        for month in months:
            # base tickets carry event_id=None by construction (sampler default)
            specs.extend(sample_month(year, month, per_month, seed=seed))
    return specs


def _outage_specs(rng, event) -> list[TicketSpec]:
    """Sharp spike: ~80% of the extra tickets in the first 2 days, tail after."""
    start = datetime.fromisoformat(event.start)
    boost = [SCEN_BY_ID[b] for b in event.boost]
    specs: list[TicketSpec] = []
    for _ in range(event.magnitude):
        # front-load: most tickets in the first 2 days, the rest across the tail
        if event.duration_days <= 2 or rng.random() < 0.80:
            day = rng.random() * min(2, event.duration_days)
        else:
            day = 2 + rng.random() * (event.duration_days - 2)
        dt = start + timedelta(days=day, seconds=rng.random() * 86_400)
        scenario = rng.choice(boost)  # error-report scenarios only
        specs.append(_build_spec(rng, scenario, dt,
                                 event_id=event.event_id, event_type="outage"))
    return specs


def _launch_specs(rng, event) -> list[TicketSpec]:
    """Gradual wave + pre-launch feature-request ramp for a new connector."""
    start = datetime.fromisoformat(event.start)
    feat = event.feature
    n_pre = round(event.magnitude * PRELAUNCH_SHARE)
    n_wave = event.magnitude - n_pre
    specs: list[TicketSpec] = []

    # Pre-launch: "when will you add connector X?" — ramps up toward the launch
    # date (denser near `start`) and stops there. This is the falling-request arc.
    fr_scenario = SCEN_BY_ID[FEATURE_REQUEST_SCENARIO]
    for _ in range(n_pre):
        frac = rng.random() ** 0.5  # skew toward 1 -> denser close to launch
        dt = start - timedelta(days=event.prelaunch_days * (1 - frac))
        seed = f"asks when a direct {feat} connector will be available (it does not exist yet)"
        specs.append(_build_spec(rng, fr_scenario, dt, seed_text=seed,
                                 event_id=event.event_id, event_type="launch"))

    # Post-launch how-to wave: 60/25/15 across three months, biased to the
    # connector's how-to scenarios, with the feature named in the seed.
    boost = [SCEN_BY_ID[b] for b in event.boost]
    for _ in range(n_wave):
        month = rng.choices((0, 1, 2), weights=WAVE_MONTH_SPLIT, k=1)[0]
        dt = start + timedelta(days=month * 30 + rng.random() * 30,
                               seconds=rng.random() * 86_400)
        scenario = rng.choice(boost)
        if "reauthorize" in scenario.id:
            seed = f"the {feat} connector is disabled — how to enable it (needs Admin on the org)"
        else:
            seed = f"asks how to connect the newly launched {feat} connector"
        specs.append(_build_spec(rng, scenario, dt, seed_text=seed,
                                 event_id=event.event_id, event_type="launch"))
    return specs


def generate_plan(seed: int = 11) -> list[TicketSpec]:
    """Return the full chronologically-numbered ticket plan (base + events)."""
    specs = _base_specs(seed)
    rng = random.Random(f"{seed}-events")
    for event in EVENTS:
        if event.event_type == "outage":
            specs.extend(_outage_specs(rng, event))
        else:
            specs.extend(_launch_specs(rng, event))

    # keep everything inside the span, then number globally by time (like a real
    # ticketing system: TCK-000001 is the earliest ticket overall).
    specs = [s for s in specs
             if SPAN_START <= datetime.fromisoformat(s.created_at) < SPAN_END]
    specs.sort(key=lambda s: s.created_at)
    return [replace(s, ticket_id=f"TCK-{i + 1:06d}") for i, s in enumerate(specs)]


if __name__ == "__main__":
    plan = generate_plan()
    n = len(plan)
    n_event = sum(1 for s in plan if s.event_id)
    print(f"total tickets: {n}")
    print(f"event-driven:  {n_event}  ({n_event / n * 100:.1f}%)   (target 20-30%)\n")

    # monthly volume: base vs event — should be flat-ish growth with visible
    # spikes at outage months and waves at launch months.
    total_by_month = Counter(s.created_at[:7] for s in plan)
    event_by_month = Counter(s.created_at[:7] for s in plan if s.event_id)
    print("month     total  event")
    for m in sorted(total_by_month):
        bar = "#" * (event_by_month[m] // 15)
        print(f"{m}  {total_by_month[m]:5d}  {event_by_month[m]:5d}  {bar}")

    # pre/post-launch feature-request signal: requests for connector X should be
    # present before its launch and ~0 after (the falling-request arc).
    print("\nfeature-request arc (should drop to ~0 after each launch):")
    launches = [e for e in EVENTS if e.event_type == "launch"]
    for e in launches:
        start = e.start
        before = sum(1 for s in plan
                     if s.event_id == e.event_id
                     and s.scenario_id == FEATURE_REQUEST_SCENARIO
                     and s.created_at < start)
        after = sum(1 for s in plan
                    if s.event_id == e.event_id
                    and s.scenario_id == FEATURE_REQUEST_SCENARIO
                    and s.created_at >= start)
        print(f"  {e.feature:<16} start {start}  before={before:4d}  after={after:3d}")
