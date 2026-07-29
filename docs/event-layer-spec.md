# Event Layer — Specification

Status: **draft** (in progress)
Scope: the temporal event layer added on top of the v1 synthetic ticket flow to
produce the 18k dataset.

---

## 1. Problem & objective

The v1 dataset generates every ticket independently: each one draws its scenario
from the catalog with a die roll, with no memory of what came before. That yields
labels that are coherent per-ticket, but a **flat temporal flow** — Monday looks
like Tuesday, January like July. Real support does not behave that way: a spike of
"dashboard won't load" tickets arrives when there is a service outage, or a wave of
setup questions arrives when a new feature ships.

The event layer adds that temporal correlation. An **event** is an external cause,
bounded in time, that pushes the volume and the nature of tickets during a window.

The objective is twofold:

1. **Realism for the EDA** — the 18k dataset shows a temporal signature (spikes,
   waves, seasonality) that an analyst would recognize, instead of white noise.
2. **Unlock time-series use cases** — with realistic spikes, the dataset can also
   train/demonstrate **forecasting** (predict next week's ticket volume for
   staffing) and **anomaly detection** (alarm when today's volume is 3x normal
   because something broke). Neither is learnable from a flat flow. This is
   documented as an intended use even if the model itself is built later.

### Architecture: two layers, additive

The generator is **not** one monolithic flow. It is two independent layers:

- **Base flow** — the existing v1 sampler + scenario catalog. Produces a steady
  background of tickets, evenly across the calendar. Left untouched.
- **Event layer** — sits on top. Each event injects an *extra* batch of tickets
  into its window, biased toward its own topic/priority/sentiment. The base keeps
  running underneath, unaware of the events.

Composition rule: an event **adds** volume (never replaces the base) and **biases**
the labels of the extra tickets it creates. This separation is deliberate — the
base already works and stays intact, and the event layer can be tested in isolation
(generate base → measure; add events → measure; the delta *is* the proof).

---

## 2. What is an event

An event is an external cause bounded in time. Model:

| Field         | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| `event_id`    | stable key, e.g. `launch_salesforce_connector`                 |
| `event_type`  | `outage` or `launch`                                           |
| `start_date`  | when the event begins                                          |
| `duration`    | how long its influence lasts (days for outage, months for launch) |
| `magnitude`   | how many extra tickets it injects over its window              |
| `topic_bias`  | which topic/scenario the extra tickets lean toward             |

Each ticket created by an event is tagged with its `event_id` and `event_type`
(these are the fields reserved as null in v1). Base-flow tickets keep them null.

---

## 3. Event types

### 3.1 Outage — sharp spike

A service breaks; tickets surge for a few days, then stop when it is fixed.

- Shape: **sharp spike**, front-loaded (~80% of the extra tickets in the first
  couple of days), then a fast tail.
- Duration: days (short).
- Bias: existing "broken" scenarios — high priority, negative sentiment. E.g.
  `connectors_sync_broken` (a connector sync outage), `dashboards_not_loading`
  (a dashboard load outage).

### 3.2 Launch — gradual wave

A new feature ships; questions arrive as adoption ramps, then taper.

- Shape: **decay over ~3 months**, roughly 60% / 25% / 15% by month.
- Duration: months (long).
- Bias: `how_to` and `misconfiguration` about the new feature, low/medium
  priority, neutral/curious sentiment.

**Launch features** (grounded in the product — Polaris is a marketing-analytics
SaaS; connectors are data sources). Currently existing (have KB articles): **GA4,
HubSpot**. The launches ship these new connectors:

1. **Salesforce connector**
2. **Zoho CRM connector**
3. **TikTok Ads connector**

**Full arc** (approved): each launch has a *before* and an *after*.

- **Before the launch** — feature-request tickets from users who have **no native
  connector to their CRM** and ask *"when will you add a direct Salesforce / Zoho
  connector?"* (scenario `connectors_feature_request_source`, with the launch's
  `feature` name injected). These fall off to ~0 right when the connector ships.
- **The launch** — the wave of `how_to` / `misconfiguration` tickets about the new
  connector, following the 60/25/15 decay.

The falling feature-requests + rising how-to wave give the dataset a precise
temporal signal that pivots exactly on the launch date.

---

## 4. Coupling with tickets

An event does **not** invent new labels. It does exactly two things inside its
window:

1. **Extra volume** — it injects an additional batch of tickets on top of the base
   flow (`magnitude`, shaped by the event's time curve).
2. **Temporal reweighting of the scenario catalog** — during the window, the event
   raises the sampling weight of the scenarios it is about (and, for a launch, can
   lower others such as the pre-launch feature requests).

Priority and sentiment are **inherited for free** from the biased scenarios. The
scenario catalog already encodes topic × type × priority × routing × sentiment
coherently, so reweighting *which* scenarios fire is enough — the event never sets
priority/sentiment independently, which removes any risk of incoherent labels.

Mental model: the scenario catalog is a weighted roulette. The base flow spins it
with its normal weights; an event, during its window, stacks extra chips on a few
pockets.

- **GA4 outage** → weight of `connectors_sync_broken` spikes (already
  priority=high, negative sentiment).
- **Salesforce launch** → weight of `connectors_howto_connect_*` rises while
  `connectors_feature_request_source` for Salesforce falls.

---

## 5. Global parameters

- **Total:** ~18,000 tickets.
- **Span:** calendar years 2024 + 2025, with 2025 at ~2x the volume of 2024
  (company growing). Roughly 6k in 2024, 12k in 2025.
- **Event share:** ~25% of all tickets are event-driven (inside the 20–30% band);
  the remaining ~75% is base flow.
- **Launches:** 3 total, one per new connector, spread across the span:
  - Salesforce connector → Q2 2024
  - Zoho CRM connector → Q4 2024
  - TikTok Ads connector → Q2 2025
- **Outages:** recurring, ~3 per year (~6 total), in varied months. Each is one of
  two flavors: a connector-sync outage (GA4/HubSpot) or a dashboards outage.

---

## 6. Acceptance criteria

1. The base-only EDA is flat (near-uniform volume over time); base+events shows
   **visible spikes** at outage dates and **waves** at launch dates.
2. Feature-request tickets for connector X **drop to ~0 right after** X's launch
   date (proof of the full arc).
3. The share of tickets carrying an `event_id` lands in the **20–30%** band.
4. Inside outage windows, the priority/sentiment distribution **skews** toward
   high / negative (inherited from the biased scenarios, not forced).
