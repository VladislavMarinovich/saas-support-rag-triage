"""
Taxonomy + scenario catalog for the synthetic Polaris support tickets.

This module is PURE DATA (no LLM, no I/O): it declares the label spaces, the
metadata distributions, the picklist-noise weights, and the SCENARIO CATALOG
that the sampler (next step) draws from.

Design (see docs/dataset-spec.md §4 and docs/product-polaris.md):
  A scenario is one canonical support situation that already carries its
  coherent ground-truth labels (topic/type/priority/routing) plus the sentiments
  that fit it and a short `seed` used to prompt the LLM. The sampler picks a
  scenario by weight, then varies the SURFACE (sentiment, role, plan, channel,
  length, phrasing) so the same scenario yields many different-looking tickets.

  Why a catalog instead of branchy rules: it keeps label combinations coherent
  by construction, it is trivial to review against the product doc, and it is
  the only clean way to reach all five routing buckets (upgrade -> sales,
  cancel -> retention) which a flat (topic, type) mapping cannot express.

Run `python -m src.taxonomy` to print the label marginals and sanity-check that
priority lands near the target 60 / 30 / 9 / 1 mix.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Label spaces (the ML prediction targets) — dataset-spec.md §5.1
# ---------------------------------------------------------------------------
TOPICS = (
    "connectors", "dashboards", "northstar", "alerts",
    "reports", "attribution", "users_workspace", "billing",
)
TYPES = (
    "bug", "outage", "misconfiguration", "how_to",
    "feature_request", "feedback", "security", "billing",
)
PRIORITIES = ("low", "medium", "high", "critical")
ROUTINGS = (
    "kb_autoresolve", "engineering", "sales_success",
    "retention", "security_incident",
)
SENTIMENTS = ("neutral", "confused", "overwhelmed", "frustrated", "angry", "anxious")

# ---------------------------------------------------------------------------
# Intake input (NOT a target) — the user's own picklist choice — §5.2
# Coarse and area-mixed on purpose: this is what a real customer-facing dropdown
# looks like, not the clean internal taxonomy.
# ---------------------------------------------------------------------------
REPORTED_CATEGORIES = (
    "connectors_integrations", "dashboards_reports", "attribution", "alerts",
    "account_billing", "users_access", "bug_something_broken",
    "how_to_question", "security_concern", "other",
)

# How the user's picklist choice is corrupted relative to the true labels — §4.6.
# The sampler consumes these weights; ~35% total intake error is the headroom the
# triage model gets to "correct" (a value story, not just noise).
REPORTED_CATEGORY_NOISE = {
    "aligned": 0.65,   # picks a category that matches the true topic/type
    "wrong": 0.25,     # picks a plausible-but-wrong category
    "other": 0.10,     # gives up and picks the catch-all
}

# ---------------------------------------------------------------------------
# Metadata distributions — dataset-spec.md §1 / §2
# (relative weights; the sampler normalizes them)
# ---------------------------------------------------------------------------
PLAN_WEIGHTS = {"starter": 0.50, "growth": 0.35, "enterprise": 0.15}
CHANNEL_WEIGHTS = {"email": 0.50, "chat": 0.35, "in_app": 0.15}
ROLE_WEIGHTS = {"admin": 0.35, "analyst": 0.40, "viewer": 0.25}
# Body length band -> probability (calibrated on the Kaggle EDA, mean ~417 chars).
LENGTH_WEIGHTS = {"short": 0.25, "medium": 0.55, "long": 0.20}

# ---------------------------------------------------------------------------
# Scenario catalog
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Scenario:
    """One canonical support situation with its coherent ground-truth labels."""
    id: str                      # stable key, e.g. "connectors_ga4_auth_expired"
    topic: str                   # target label (must be in TOPICS)
    type: str                    # target label (must be in TYPES)
    priority: str                # target label (must be in PRIORITIES)
    routing: str                 # target label (must be in ROUTINGS)
    sentiments: tuple[str, ...]  # sentiments that plausibly fit this situation
    seed: str                    # short situation description that seeds the prompt
    weight: float                # relative frequency (drives the label marginals)
    roles: tuple[str, ...] | None = None  # restrict user_role when it matters (None = any)


# NOTE ON WEIGHTS: chosen so the *priority* marginal lands near 60/30/9/1 and
# kb_autoresolve is the largest routing bucket (the RAG-deflection story). The
# `__main__` block below prints the actual marginals so we can verify/tune.
SCENARIOS: tuple[Scenario, ...] = (
    # --- LOW: how-to questions (deflectable via KB) ------------------------
    Scenario("connectors_howto_connect_hubspot", "connectors", "how_to", "low",
             "kb_autoresolve", ("neutral", "confused"),
             "asks how to connect the HubSpot connector", 6.0),
    Scenario("connectors_howto_reauthorize", "connectors", "how_to", "low",
             "kb_autoresolve", ("neutral", "confused"),
             "asks how to reauthorize an expired connector", 6.0, roles=("admin",)),
    Scenario("dashboards_howto_build", "dashboards", "how_to", "low",
             "kb_autoresolve", ("neutral", "confused", "overwhelmed"),
             "asks how to build a dashboard from scratch", 6.0),
    Scenario("northstar_howto_define", "northstar", "how_to", "low",
             "kb_autoresolve", ("neutral", "confused"),
             "asks how to define their north-star metric", 3.0),
    Scenario("alerts_howto_create", "alerts", "how_to", "low",
             "kb_autoresolve", ("neutral", "confused"),
             "asks how to create an alert", 5.0),
    Scenario("reports_howto_export_csv", "reports", "how_to", "low",
             "kb_autoresolve", ("neutral",),
             "asks how to export a report to CSV", 5.0),
    Scenario("attribution_howto_which_model", "attribution", "how_to", "low",
             "kb_autoresolve", ("neutral", "confused"),
             "asks which attribution model Polaris uses", 5.0),
    Scenario("users_howto_invite_team", "users_workspace", "how_to", "low",
             "kb_autoresolve", ("neutral", "overwhelmed"),
             "asks how to invite teammates and set their roles", 5.0),
    Scenario("billing_howto_plan_contents", "billing", "how_to", "low",
             "kb_autoresolve", ("neutral",),
             "asks what is included in the Growth plan", 4.0),
    # --- LOW: feature requests (logged to the product/eng backlog) ---------
    Scenario("alerts_feature_request_slack", "alerts", "feature_request", "low",
             "engineering", ("neutral", "frustrated"),
             "requests Slack delivery for alerts (not available today)", 5.0),
    Scenario("connectors_feature_request_source", "connectors", "feature_request", "low",
             "engineering", ("neutral",),
             "requests a new data source connector that does not exist yet", 3.0),
    # --- LOW: feedback / complaint (relationship owned by Success) ----------
    Scenario("dashboards_feedback_ui", "dashboards", "feedback", "low",
             "sales_success", ("frustrated", "neutral"),
             "general feedback that the dashboard UI is confusing", 7.0),

    # --- MEDIUM: misconfiguration (user setup — resolved by guidance) ------
    Scenario("connectors_ga4_auth_expired", "connectors", "misconfiguration", "medium",
             "kb_autoresolve", ("confused", "frustrated"),
             "GA4 connector auth expired and they cannot reconnect (needs Admin+)",
             5.0, roles=("viewer", "analyst")),
    Scenario("attribution_no_utms", "attribution", "misconfiguration", "medium",
             "kb_autoresolve", ("confused", "frustrated"),
             "attribution report is empty because there are no UTMs / GA4 not connected",
             5.0),
    Scenario("alerts_threshold_wrong", "alerts", "misconfiguration", "medium",
             "kb_autoresolve", ("confused", "neutral"),
             "alert threshold was set wrong so it fires incorrectly", 4.0),
    Scenario("reports_wrong_recipient", "reports", "misconfiguration", "medium",
             "kb_autoresolve", ("confused", "frustrated"),
             "scheduled report goes to the wrong recipient (misconfigured email)", 3.0),
    Scenario("users_role_misassigned", "users_workspace", "misconfiguration", "medium",
             "kb_autoresolve", ("confused",),
             "a teammate was given the wrong role and cannot see what they expect", 3.0),
    # --- MEDIUM: single-feature bugs (real defects, go to engineering) -----
    Scenario("alerts_not_firing_bug", "alerts", "bug", "medium",
             "engineering", ("frustrated", "neutral"),
             "an alert is not firing when its condition is clearly met", 3.0),
    Scenario("reports_delivery_error", "reports", "bug", "medium",
             "engineering", ("frustrated",),
             "a scheduled report did not arrive due to a real delivery error", 3.0),
    Scenario("dashboards_widget_bug", "dashboards", "bug", "medium",
             "engineering", ("frustrated", "neutral"),
             "a dashboard widget renders incorrectly (visual bug)", 2.0),
    Scenario("connectors_sync_delay", "connectors", "bug", "medium",
             "engineering", ("frustrated", "confused"),
             "a connector sync is lagging so data looks slightly stale", 2.0),

    # --- HIGH: decision-impacting or revenue/retention ---------------------
    Scenario("connectors_sync_broken", "connectors", "bug", "high",
             "engineering", ("frustrated", "angry"),
             "connector sync is broken and stale data is affecting decisions", 2.0),
    Scenario("dashboards_wrong_numbers", "dashboards", "bug", "high",
             "engineering", ("frustrated", "angry"),
             "a dashboard is showing numbers the customer knows are wrong", 2.0),
    Scenario("billing_overcharge", "billing", "billing", "high",
             "sales_success", ("angry", "frustrated"),
             "the customer was double-charged / overcharged on their invoice", 1.5),
    Scenario("billing_upgrade_request", "billing", "billing", "high",
             "sales_success", ("neutral",),
             "the customer wants to upgrade / expand their plan (revenue)", 2.0),
    Scenario("billing_cancel_request", "billing", "billing", "high",
             "retention", ("frustrated", "neutral", "angry"),
             "the customer wants to cancel or downgrade (churn risk)", 1.5),

    # --- CRITICAL: systemic / security / outage (rare) ---------------------
    Scenario("dashboards_outage", "dashboards", "outage", "critical",
             "security_incident", ("angry", "anxious", "frustrated"),
             "dashboards are fully down; the customer cannot see any metrics", 0.25),
    Scenario("northstar_metric_miscalc", "northstar", "bug", "critical",
             "engineering", ("angry", "anxious"),
             "the north-star metric is miscalculated — wrong everywhere (systemic)", 0.25),
    Scenario("users_cross_tenant_leak", "users_workspace", "security", "critical",
             "security_incident", ("anxious", "angry"),
             "the customer can see another organization's data (cross-tenant leak)", 0.25),
    Scenario("users_access_breach", "users_workspace", "security", "critical",
             "security_incident", ("anxious", "angry"),
             "the customer reports unauthorized access / possible data exposure", 0.25),
)


# ---------------------------------------------------------------------------
# Verification helper — prints the label marginals implied by the weights.
# ---------------------------------------------------------------------------
def _marginals(key) -> list[tuple[str, float]]:
    """Return [(label, share)] over SCENARIOS weighted by scenario weight."""
    total = sum(s.weight for s in SCENARIOS)
    acc: dict[str, float] = {}
    for s in SCENARIOS:
        acc[key(s)] = acc.get(key(s), 0.0) + s.weight
    return sorted(((k, v / total) for k, v in acc.items()), key=lambda kv: -kv[1])


if __name__ == "__main__":
    print(f"scenarios: {len(SCENARIOS)}   total weight: {sum(s.weight for s in SCENARIOS):.2f}\n")
    for dim, key in (
        ("priority", lambda s: s.priority),
        ("routing", lambda s: s.routing),
        ("type", lambda s: s.type),
        ("topic", lambda s: s.topic),
    ):
        print(dim)
        for label, share in _marginals(key):
            print(f"  {label:<18} {share * 100:5.1f}%")
        print()
