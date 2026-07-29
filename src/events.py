"""
Event catalog for the temporal event layer (see docs/event-layer-spec.md).

This module is PURE DATA (no LLM, no I/O), the sibling of src/taxonomy.py: it
declares the concrete EVENTS that sit on top of the base ticket flow and give the
18k dataset a realistic temporal signature — sharp outage spikes and gradual
launch waves.

Design (event-layer-spec.md §2–§4):
  An event is an external cause bounded in time. It does two things inside its
  window: it INJECTS extra tickets (`magnitude`, shaped by a time curve implied by
  `event_type`) and it REWEIGHTS the scenario catalog toward the scenarios in
  `boost`. Priority/sentiment are inherited from those scenarios — the event never
  sets labels itself, so combinations stay coherent by construction.

  Two shapes, implied by `event_type`:
    - outage : sharp, front-loaded spike over a few DAYS (a service breaks).
    - launch : gradual 60/25/15 decay over ~3 MONTHS (a new feature ships).

  The launch full arc: `feature` names the new connector, and `prelaunch_days`
  marks how long BEFORE `start` the "please add connector X" feature requests ramp
  up — they fall to ~0 at `start`, when the how-to wave takes over.

  NOTE (generator dependency): the scenario catalog only has connector how-to
  seeds for existing connectors (HubSpot, GA4). A launch reuses those generic
  scenarios but its `feature` string must be injected into the prompt so the
  ticket body is about the launched connector (Salesforce/Zoho/TikTok), not
  HubSpot. The generator (next step) is responsible for that substitution.

Run `python -m src.events` to validate the catalog and print the event-driven
share against the ~18k / ~25% target.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.taxonomy import SCENARIOS

EVENT_TYPES = ("outage", "launch")


@dataclass(frozen=True)
class Event:
    """One canonical external event that perturbs the base ticket flow."""
    event_id: str                # stable key, e.g. "launch_salesforce_connector"
    event_type: str              # "outage" or "launch" (implies the time curve)
    start: str                   # ISO date the event begins, "YYYY-MM-DD"
    duration_days: int           # length of the influence window (days)
    magnitude: int               # extra tickets injected over the window
    boost: tuple[str, ...]       # scenario ids whose weight rises during the window
    feature: str | None = None   # new connector name (launches); injected into prompts
    prelaunch_days: int = 0      # days before `start` the feature-requests ramp (launches)


# ---------------------------------------------------------------------------
# Event catalog — 3 launches + 6 outages, spread across 2024–2025.
# 2025 magnitudes run ~2x 2024 (the company is growing; see spec §5).
# ---------------------------------------------------------------------------
EVENTS: tuple[Event, ...] = (
    # --- LAUNCHES: new connectors ship, how-to waves follow (60/25/15) ------
    # All three ship in 2025, in sequence: Salesforce (Q1/Q2) -> TikTok (Q2)
    # -> Zoho (Q3/Q4). 2024 carries no launches (a stable-product year).
    Event("launch_salesforce_connector", "launch", "2025-03-03", 90, 800,
          boost=("connectors_howto_connect_hubspot", "connectors_howto_reauthorize"),
          feature="Salesforce", prelaunch_days=90),
    Event("launch_tiktok_connector", "launch", "2025-05-12", 90, 1200,
          boost=("connectors_howto_connect_hubspot", "connectors_howto_reauthorize"),
          feature="TikTok Ads", prelaunch_days=90),
    Event("launch_zoho_connector", "launch", "2025-09-15", 90, 800,
          boost=("connectors_howto_connect_hubspot", "connectors_howto_reauthorize"),
          feature="Zoho CRM", prelaunch_days=90),

    # --- OUTAGES 2024: sharp spikes over a few days -------------------------
    Event("outage_ga4_sync_2024q1", "outage", "2024-02-20", 4, 200,
          boost=("connectors_sync_broken", "connectors_sync_delay")),
    Event("outage_dashboards_2024q3", "outage", "2024-07-09", 3, 200,
          boost=("dashboards_outage", "dashboards_wrong_numbers")),
    Event("outage_hubspot_sync_2024q4", "outage", "2024-11-05", 4, 200,
          boost=("connectors_sync_broken", "connectors_sync_delay")),

    # --- OUTAGES 2025: same shapes, ~2x magnitude ---------------------------
    Event("outage_dashboards_2025q1", "outage", "2025-03-12", 3, 400,
          boost=("dashboards_outage", "dashboards_wrong_numbers")),
    Event("outage_ga4_sync_2025q3", "outage", "2025-08-19", 4, 400,
          boost=("connectors_sync_broken", "connectors_sync_delay")),
    Event("outage_dashboards_2025q4", "outage", "2025-11-04", 3, 400,
          boost=("dashboards_outage", "dashboards_wrong_numbers")),
)


# ---------------------------------------------------------------------------
# Verification helper — validates every event and prints the coverage totals.
# ---------------------------------------------------------------------------
def validate_catalog() -> None:
    """Fail loudly if any event references an unknown type or scenario id."""
    scenario_ids = {s.id for s in SCENARIOS}
    for e in EVENTS:
        assert e.event_type in EVENT_TYPES, f"{e.event_id}: bad type {e.event_type}"
        # every boosted scenario must exist in the taxonomy catalog
        for sid in e.boost:
            assert sid in scenario_ids, f"{e.event_id}: unknown scenario {sid}"
        # launches carry a feature name; outages do not
        if e.event_type == "launch":
            assert e.feature, f"{e.event_id}: launch needs a feature name"


if __name__ == "__main__":
    validate_catalog()
    # extra tickets the layer injects vs the ~18k / ~25% target
    total_events = sum(e.magnitude for e in EVENTS)
    target_total = 18_000
    print(f"events: {len(EVENTS)}   event-driven tickets: {total_events}")
    print(f"event share of {target_total}: {total_events / target_total * 100:.1f}%  (target 20-30%)\n")

    # split the injected volume by year and by type (sanity vs the 2x-in-2025 plan)
    by_year: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for e in EVENTS:
        by_year[e.start[:4]] = by_year.get(e.start[:4], 0) + e.magnitude
        by_type[e.event_type] = by_type.get(e.event_type, 0) + e.magnitude
    print("by year:", {y: by_year[y] for y in sorted(by_year)})
    print("by type:", by_type)
