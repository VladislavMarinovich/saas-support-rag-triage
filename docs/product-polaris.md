# Polaris — Product Reference

> **Fictional** analytics SaaS used to ground the support triage + RAG demo.
> Not a real product. Content is synthetic; the pipeline is real.
> This file is the single source of truth for the "topic" axis, the failure
> modes, and the routing/priority logic that the ticket generator and the
> knowledge base derive from.

## What Polaris is

Polaris unifies your marketing & revenue data (Google Ads, GA4, CRM, email
platforms) into one place — dashboards, alerts, attribution, and a north-star
metric tracker.

## Architecture (this is what generates the failure modes)

- **Multi-tenant** — each customer is a *workspace* (tenant); users belong to a
  tenant. Failure classes: cross-tenant data leak, wrong-tenant assignment,
  seeing another org's data.
- **Connectors** — OAuth integrations to external sources (Google Ads, GA4,
  HubSpot/Salesforce, Mailchimp/Brevo). Failure classes: auth expired, sync
  failed, partial/stale data. Reconnecting is **permission-gated** (Admin+).
- **Data freshness** — data syncs on a schedule (hourly/daily). Failure classes:
  stale data, sync lag, discrepancy vs the source.
- **Roles & permissions** — Admin / Analyst / Viewer. Failure classes: permission
  denied, can't access a dashboard, visibility issues.
- **Billing & plans + seats** — Failure classes: overcharge, seat limit,
  plan changes.

## Plans

| Plan | Positioning |
|---|---|
| Starter | Few connectors, small seat count, short data retention |
| Growth | More connectors, more seats, longer retention |
| Enterprise | Unlimited connectors, SSO, priority support, full retention |

## Features (the "topic" axis)

1. Connectors
2. Dashboards
3. North-Star Metric tracker
4. Alerts
5. Reports / scheduled exports
6. Attribution / data blending
7. Users & Workspace (multi-tenant)
8. Billing

## Ticket model

Every synthetic ticket is characterized by five single-label dimensions:

```
topic  ×  type  ×  priority  ×  routing  ×  sentiment
```

Richness comes from **combining** dimensions, not from stacking multiple tags.

### Type taxonomy

| Type | Notes |
|---|---|
| Bug / Error | Something in Polaris misbehaves |
| Outage / Incident | Feature(s) down |
| Misconfiguration (user setup) | The customer's setup is wrong (e.g., no UTMs, GA4 not connected) — **resolved by guidance, not engineering** |
| How-to / Question | Informational request |
| Feature request | Not available today → logged in the feature backlog |
| Feedback / Complaint | Opinion, dissatisfaction |
| Security | Breach, access control, data exposure |
| Billing | Charges, seats, plan changes |

### Priority logic (technical **and** business)

| Priority | Triggers |
|---|---|
| **critical** | Outage; security breach; cross-tenant data leak; **metric miscalculation** (rare but systemic — wrong everywhere); dashboards fully down (can't see metrics to decide) |
| **high** | Sync broken affecting decisions; wrong dashboard numbers; billing overcharge; **upgrade / expansion request (= revenue)**; **cancellation / downgrade (= churn risk)** |
| **medium** | Single-feature bug; alert misfire; misconfiguration; report not arriving |
| **low** | How-to; feature request; feedback |

> **Business overlay:** priority is not only technical urgency. An upgrade is
> high (revenue), a cancellation is high (retention) — even though neither is a
> technical fault. Sentiment can bump priority (see below) but does not set the
> base.

### Routing targets

- **KB / auto-resolve** — misconfiguration, how-to (the RAG-deflection star case)
- **Engineering** — real bugs, outages
- **Sales / Success** — upgrades, expansion
- **Retention** — cancellations, downgrades
- **Security / Incident** — breach, outage

### Sentiment

| Sentiment | Effect on handling |
|---|---|
| Neutral | Standard (most how-to) |
| Confused | Clarify via KB |
| Overwhelmed | Offer onboarding / academy → route to Success (needs education, not a fix) |
| Frustrated | Something's not working; annoyed |
| Angry | **Bump priority** + careful, apologetic tone (typical with inconsistent data) |
| Anxious | Reassure; prioritize if security-related |

## Feature × failure-mode map

| Feature | Bug / Outage | Misconfiguration | How-to |
|---|---|---|---|
| Connectors | GA4 stopped syncing; auth expired | Expired + can't reconnect (needs Admin+) | "How do I connect HubSpot?" |
| Dashboards | Won't load (**critical** — blocks decisions); wrong numbers | — | "How do I build a dashboard?" |
| North-Star | Metric miscalculated (**critical** — systemic) | — | "How do I define my north-star?" |
| Alerts | Doesn't fire / false alarm (**medium**) | Threshold set wrong (guide is enough) | "How do I create an alert?" |
| Reports | Scheduled report didn't arrive — dual branch: (a) wrong email set → guide; (b) real delivery error / 400 → engineering | Wrong recipient configured | "How do I export to CSV?" |
| Attribution | Polaris miscalculated | **No UTMs / GA4 not connected** (user setup — RAG guidance) | "Which attribution model do you use?" |
| Users / Workspace | Sees another tenant's data (**critical**); permission denied; SSO | Role misassigned | "How do I invite my team?" |
| Billing | Double charge; seat limit reached | — | "What's in the Growth plan?"; upgrade/cancel requests |

## Out of scope (v2 backlog)

- Multi-label ticket tags (v1 is single-label per dimension for clean evals)
- Additional sentiments
- Additional features / deeper plan differences
- Real multi-language (v1 is English only)
