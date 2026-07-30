# Polaris Support Tickets (Synthetic, v2)

~24,000 synthetic customer-support tickets for **Polaris**, a fictional
multichannel analytics SaaS. Each ticket carries coherent ground-truth labels for
**triage** (topic · type · priority · routing · sentiment) plus a noisy intake
category, spanning **Jan 2024 → Jun 2026** with a realistic **temporal event
layer** (service outages and product launches).

> Synthetic data, generated on a real pipeline. **No real users, no PII.**

## Why this dataset

Most public support datasets are tiny, unlabeled, or class-balanced by design —
which hides the two things that make real triage hard: **noisy intake** (customers
mis-categorize their own tickets ~35% of the time) and **temporal clustering**
(incidents and launches produce bursts of similar tickets). This set exposes both,
so it drives three tasks from one corpus:

- **Triage classification** — predict the true labels from raw text.
- **RAG deflection** — the `kb_autoresolve` mass is where a grounded assistant helps.
- **Time-series** — outage spikes and launch waves make volume forecasting and
  anomaly detection learnable.

## Files

- `polaris_tickets_v2.parquet` / `polaris_tickets_v2.csv` — one row per ticket.

## Columns

| Column | Kind | Notes |
|---|---|---|
| `ticket_id`, `created_at` | metadata | id · ISO 8601 |
| `channel`, `plan`, `user_role` | input | email/chat/in_app · starter/growth/enterprise · admin/analyst/viewer |
| `reported_category` | input · **noisy** | the customer's own dropdown pick — wrong ~35% of the time |
| `subject`, `body` | input · **text** | the ticket the model reads |
| `topic`, `type`, `priority`, `routing`, `sentiment` | **targets** | coherent ground-truth triage labels |
| `event_id`, `event_type` | metadata | non-null for event-driven tickets (`outage` / `launch`) |

## How it was built

Scenario catalog → seeded sampler → LLM writer (Gemini on Vertex AI), plus an
additive **event layer**: outages (sharp spikes) and launches (gradual waves,
preceded by "when will you add X?" feature-requests that drop to zero on launch
day). ~25% of tickets are event-driven; ~75% is baseline flow.

## Honest caveats

- **Synthetic signal** — text maps to labels cleanly by construction, so classifier
  scores run high (~0.99 on easy labels). Expect lower on real tickets: this
  demonstrates a *pipeline and method*, not an infallible model.
- Baseline volume is annual-scaled (flat within a year, steps at year boundaries).
- English only; a single fictional product.

## Full pipeline, EDA & modeling

Code, exploratory analysis, a learning curve, and a documented label-quality audit:
https://github.com/VladislavMarinovich/saas-support-rag-triage

**License:** CC BY-SA 4.0. **Citation:** Marinovich, V. (2026). *Polaris Support
Tickets — Synthetic Dataset (v2).*
