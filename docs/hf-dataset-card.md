---
license: cc-by-sa-4.0
task_categories:
  - text-classification
  - question-answering
language:
  - en
tags:
  - customer-support
  - synthetic
  - triage
  - rag
  - time-series
size_categories:
  - 10K<n<100K
pretty_name: Polaris Support Tickets (Synthetic, v2)
---

# Polaris Support Tickets — Synthetic Dataset (v2)

**~24,000 synthetic customer-support tickets** for *Polaris*, a fictional
multichannel analytics SaaS. Each ticket carries coherent ground-truth labels for
**triage** (topic · type · priority · routing · sentiment) plus a noisy intake
category, and the collection spans **Jan 2024 → Jun 2026** with a realistic
**temporal event layer** (service outages and product launches).

> Synthetic data, generated on a real pipeline. **No real users, no PII.** Built as
> a portfolio artifact — see the full pipeline, EDA and modeling in the
> [GitHub repo](https://github.com/VladislavMarinovich/saas-support-rag-triage).

## Why this dataset exists

Most public support datasets are either tiny, unlabeled, or *class-balanced by
design* — which hides the two things that make real triage hard: **noisy intake**
(customers mis-categorize their own tickets) and **temporal clustering** (incidents
and launches produce bursts of similar tickets). This set is built to expose both,
so it can drive three tasks from one corpus:

- **Triage classification** — predict the true labels from raw text.
- **RAG deflection** — the `kb_autoresolve` mass is where a grounded assistant helps.
- **Time-series** — outage spikes and launch waves make volume forecasting and
  anomaly detection learnable.

## Dataset structure

One JSON object per ticket. Fields:

| Field | Kind | Notes |
|---|---|---|
| `ticket_id` | id | `TCK-000001`, chronological |
| `created_at` | metadata | ISO 8601 |
| `channel`, `plan`, `user_role` | input · metadata | email/chat/in_app · starter/growth/enterprise · admin/analyst/viewer |
| `reported_category` | **input · NOISY** | the customer's own dropdown pick — wrong ~35% of the time |
| `subject`, `body` | **input · text** | the ticket the model reads |
| `topic` | **target** | 8 classes (connectors, dashboards, billing, …) |
| `type` | **target** | 8 classes (bug, outage, how_to, feature_request, security, …) |
| `priority` | **target** | low / medium / high / critical |
| `routing` | **target** | kb_autoresolve / engineering / sales_success / retention / security_incident |
| `sentiment` | **target** | operational signal (neutral … angry / anxious) |
| `event_id`, `event_type` | metadata | non-null for event-driven tickets (`outage` / `launch`) |

Two natural views: **train/eval** uses the ground-truth targets; **inference**
hides them and lets a model predict from `subject`+`body`.

## How it was built

A scenario catalog defines canonical support situations, each with coherent labels.
A seeded sampler draws scenarios and varies the surface (sentiment, role, channel,
length), then an LLM writes the customer text from a label-free prompt. On top, an
**event layer** injects bursts: **outages** (sharp spikes, ~80% in the first 2 days)
and **launches** (60/25/15 wave over 3 months, preceded by a ramp of "when will you
add X?" feature-requests that drops to zero on launch day).

## Highlights (see the repo for full EDA)

- **Event share:** ~25% of tickets are event-driven; ~75% is baseline flow.
- **Temporal signature:** visible outage spikes and launch waves; volume grows ~2x
  from 2024 to 2025.
- **Intake noise:** the customer's `reported_category` disagrees with the true
  labels ~**35%** of the time — the headroom a classifier recovers from the text.

## Data-quality note (transparency)

During review we caught a **label conflation**: `security_incident` routing had
lumped *availability* outages together with real *security* breaches, inflating the
"security" count (~841 → most were dashboards outages). We re-routed outages to
`engineering` and reserved `security_incident` for genuine breaches (~77). The
lesson — *audit the labels, not just the metric* — and the full write-up live in the
repo's classifier-evaluation notebook.

## Intended uses & limitations

**Use it for:** learning/benchmarking triage classification, RAG grounding &
honest-refusal, and time-series forecasting/anomaly detection on support volume;
teaching and demos.

**Do not** treat it as real-world ground truth. Caveats:

- **Synthetic signal.** Text maps to its label cleanly by construction, so
  classifier scores run high (~0.99 on easy labels). Expect lower on real tickets —
  this demonstrates a *pipeline and method*, not an infallible model.
- **Baseline is annual-scaled** (flat within a year, stepping at year boundaries) —
  a simplification; real volume ramps more smoothly.
- English only; a single fictional product.

## License & citation

Released under **CC BY-SA 4.0** (attribution + share-alike). If you use it:

```
Marinovich, V. (2026). Polaris Support Tickets — Synthetic Dataset (v2).
https://github.com/VladislavMarinovich/saas-support-rag-triage
```
