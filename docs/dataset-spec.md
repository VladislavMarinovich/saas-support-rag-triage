# Dataset Specification — Synthetic Support Tickets (Polaris)

> Semantic contract for the synthetic ticket dataset. Defines **what a ticket
> record contains**, **how it reads**, and **how the labels are distributed**.
> The generator code (`src/`) implements this doc; the frozen product logic
> lives in [`product-polaris.md`](product-polaris.md). Read that first — this
> file does not re-explain the taxonomy, it operationalizes it into a schema.
>
> v1 scope: **baseline layer only** (stable daily mix). The event layer
> (incidents, launches, seasonality) is v2 and only *reserves* fields here.

---

## 1. Record schema (fields)

Each ticket is one JSON object (dataset stored as JSONL). Fields split by their
**role in the ML task** — this split is the contract:

- **Inputs · text** — what the customer wrote.
- **Inputs · intake** — known at submission time, incl. the user's own picklist
  choice (which is *noisy*). System-known fields (plan/channel/role) too.
- **Targets** — the ground-truth answer key the triage model must produce.
- **Metadata** — bookkeeping + reserved event-layer fields.

| Field | Role | Type | Notes |
|---|---|---|---|
| `subject` | input · text | string | Short line, as a user titles it. May be empty for `chat`. |
| `body` | input · text | string | The customer's message. The core artifact. See §2. |
| `reported_category` | input · intake | enum(10) | **User-selected picklist at submission — NOISY.** Users mis-tag or pick `other`. The model must reconcile it, not trust it. See §5. |
| `plan` | input · intake | enum | `starter` \| `growth` \| `enterprise`. Grounds the scenario. |
| `channel` | input · intake | enum | `email` \| `chat` \| `in_app`. Affects length/formality. |
| `user_role` | input · intake | enum | `admin` \| `analyst` \| `viewer`. Gates some scenarios (reconnect needs admin+). |
| `topic` | **target** | enum(8) | True feature area. See §5. |
| `type` | **target** | enum(8) | True failure/request class. See §5. |
| `priority` | **target** | enum(4) | `low` \| `medium` \| `high` \| `critical`. Derived, see §4. |
| `routing` | **target** | enum(5) | Team / resolution path. See §5. |
| `sentiment` | **target** | enum(6) | Customer emotion. See §3. |
| `ticket_id` | meta | string | `TCK-000001` sequential. |
| `created_at` | meta | ISO datetime | Spread over the window. Drives the event layer later. |
| `event_id` | meta (v2) | string \| null | **Always null in v1.** Reserved for the event layer. |
| `event_type` | meta (v2) | enum \| null | **Always null in v1.** `incident` \| `launch` \| `seasonal`. |

### Two views of the same data

- **Train / eval (labeled):** the five **targets** are the ground-truth answer
  key. Sampling them *before* writing the text gives perfect labels for free —
  the core advantage of synthetic generation.
- **Inference / production (unlabeled):** the triage model sees only the
  **inputs** (text + intake) and *predicts* the targets. Accuracy = prediction
  vs. the hidden answer key.

`reported_category` is deliberately unreliable, so the demo can show a real value
story: **users mis-classify their own tickets; the model corrects them.**

---

## 2. Language & style

- **English only** (v1). Real multi-language is v2 backlog.
- **Voice = real inbound support, not marketing copy.** Customers are annoyed,
  rushed, and imprecise. The source datasets (Bitext) are *too clean*; we inject
  realism deliberately.
- **Length** — calibrated on the Kaggle EDA (mean ≈ 417 chars). Target a
  distribution, not a constant:
  - short (~1 sentence / < 120 chars): ~25%
  - medium (2–4 sentences / 120–500 chars): ~55%
  - long (rant / detailed repro / > 500 chars): ~20%
  - `chat` skews short; `email` skews medium/long.
- **Realism injections** (probabilistic, not every ticket):
  - lowercase starts, missing punctuation, occasional typos
  - partial info ("it's still not working" with no detail)
  - urgency markers when priority is high/critical ("this is blocking us")
  - follow-up framing ("I already tried reconnecting")
- **Formality by role/plan** — enterprise admin reads more professional; viewer
  reads more confused/lay. Light touch, not caricature.
- **No PII** — no real names, emails, phone numbers. Use placeholders
  (`my workspace`, `our GA4 account`) or synthetic tokens. This is a published
  open dataset; PII-clean is non-negotiable.

---

## 3. Emotions (sentiment) & coupling

Six sentiments, frozen (from `product-polaris.md`). All range neutral→negative —
realistic for inbound support (nobody opens a ticket to say thanks).

| Sentiment | Typical trigger |
|---|---|
| `neutral` | how-to, plan questions, feature requests |
| `confused` | misconfiguration, "why is this happening" |
| `overwhelmed` | new user, too many features, onboarding gap |
| `frustrated` | something's broken and they're annoyed |
| `angry` | repeated failure, inconsistent data, overcharge |
| `anxious` | security / data-exposure worries |

**Sentiment is sampled *conditional* on type** (see coupling weights in §4), not
uniformly. It does **not** set base priority, but `angry` and security-related
`anxious` can **bump** priority one notch (per product logic).

---

## 4. Generative model (order + weights)

Labels are **not** five independent dice — that would produce incoherent tickets
(e.g. a `low` `outage`). We sample in dependency order so combinations stay real:

```
1. topic       ~ P(topic)                      # which feature
2. type        ~ P(type | topic)               # constrained by feature×failure map
3. priority    = f(topic, type) + overlay      # derived, mostly deterministic
4. routing     = g(type, business_branch)      # derived, deterministic
5. sentiment   ~ P(sentiment | type, priority) # emotion follows the situation
6. meta        ~ plan, role, channel, created_at
7. reported_cat~ noise(topic, type)            # the user's picklist choice, noisy
```

Steps 1–5 produce the **targets** (answer key). Step 7 produces the **noisy
intake** input — computed *after* the true labels so it can be deliberately
wrong relative to them.

### 4.1 `P(topic)` — initial weights (tune in validation)

Connectors and Attribution carry the demo's best RAG-deflection stories, so they
lead; North-Star is rare.

| topic | weight |
|---|---|
| connectors | 0.20 |
| dashboards | 0.16 |
| attribution | 0.15 |
| reports | 0.12 |
| alerts | 0.11 |
| billing | 0.11 |
| users_workspace | 0.10 |
| northstar | 0.05 |

### 4.2 `P(type | topic)`

Constrained to the pairs allowed by the **feature × failure-mode map** in
`product-polaris.md`. Across all topics the *marginal* type mix should land near:

| type | target marginal |
|---|---|
| how_to | 0.30 |
| bug | 0.20 |
| misconfiguration | 0.16 |
| feature_request | 0.10 |
| feedback | 0.10 |
| billing | 0.08 |
| outage | 0.03 |
| security | 0.03 |

### 4.3 Priority — derived, target marginal

Priority comes from the product's priority table + business overlay (upgrade /
cancel = high even without a technical fault). Sentiment bump applies after.
**Validation target** (the corrected realistic mix):

| priority | target |
|---|---|
| low | ~0.60 |
| medium | ~0.30 |
| high | ~0.09 |
| critical | ~0.01 |

> If the sampled marginal drifts from this, we tune §4.1/§4.2 weights — priority
> is the *check*, the topic/type weights are the *knobs*.

### 4.4 Routing — deterministic

`kb_autoresolve` (how-to, misconfiguration) · `engineering` (bug, delivery-error
branch) · `sales_success` (upgrade/expansion) · `retention` (cancel/downgrade) ·
`security_incident` (security, outage). `kb_autoresolve` should be the **largest**
bucket — that is the deflection story the demo is built to show.

### 4.5 `P(sentiment | type, priority)`

Coupling (weights refined in validation):

| type | dominant sentiments |
|---|---|
| how_to | neutral, confused, overwhelmed |
| bug | frustrated, neutral, angry(if high) |
| outage | angry, anxious, frustrated |
| misconfiguration | confused, frustrated, neutral |
| feature_request | neutral, frustrated(mild) |
| feedback | frustrated, angry, neutral |
| security | anxious, angry, neutral |
| billing | frustrated(overcharge), angry, neutral(plan Q) |

### 4.6 `reported_category` noise model

The user's picklist choice maps to the *true* `topic`/`type`, then gets corrupted
to mimic real self-mis-tagging (initial weights, tune in validation):

- **aligned** (~0.65) — picks the category that matches the true topic/type.
- **wrong bucket** (~0.25) — picks a plausible-but-wrong category (e.g. a
  misconfiguration reported as `bug_something_broken`).
- **`other`** (~0.10) — gives up and picks the catch-all.

This ~35% intake error rate is the headroom the triage model gets to *correct* —
a measurable value story, not just noise.

---

## 5. Label space (enums)

### 5.1 Targets (the ML prediction targets)

Exact string values the generator emits and the classifier predicts.

- **topic** (8): `connectors` `dashboards` `northstar` `alerts` `reports` `attribution` `users_workspace` `billing`
- **type** (8): `bug` `outage` `misconfiguration` `how_to` `feature_request` `feedback` `security` `billing`
- **priority** (4): `low` `medium` `high` `critical`
- **routing** (5): `kb_autoresolve` `engineering` `sales_success` `retention` `security_incident`
- **sentiment** (6): `neutral` `confused` `overwhelmed` `frustrated` `angry` `anxious`

> Note: `billing` appears as both a topic and a type on purpose — a billing-area
> ticket is almost always a billing-type request; kept explicit for clean labels.

### 5.2 Intake input (NOT a target — noisy, model must reconcile)

- **reported_category** (10): `connectors_integrations` `dashboards_reports` `attribution` `alerts` `account_billing` `users_access` `bug_something_broken` `how_to_question` `security_concern` `other`

Coarse and area-mixed on purpose — this is what a real customer-facing picklist
looks like, not the clean internal taxonomy. It is an **input**, never scored as
an answer.

---

## 6. Out of scope (v1)

- Event layer (incidents / launches / seasonality) — fields reserved, logic is v2.
- Multi-label dimensions — single-label per axis for clean evals.
- Multi-language, additional sentiments, deeper plan differences.
- Threaded conversations / agent replies — v1 is the inbound message only.
  Threads (agent asks for a screenshot / ID / repro steps, customer replies)
  are a **response-stage** behavior, not a dataset property: they belong to the
  triage+RAG answering system (roadmap step 3), modeled later via synthetic
  follow-up turns. A `needs_more_info` flag (ground truth for "ask vs answer")
  is deferred to that stage — it is a signal for *responding*, not *classifying*.
