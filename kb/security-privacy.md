# How Polaris protects your data

Polaris is built on a **multi-tenant architecture**, meaning your workspace and data are logically isolated from every other customer's workspace. Here's how we keep your information secure:

## Isolation & access control

Each workspace is a completely separate environment. Users belong to only one workspace and cannot access another organization's dashboards, connectors, or metrics — even by accident.

**Role-based permissions** enforce who can do what:
- **Admin** — manage connectors, users, and workspace settings
- **Analyst** — build and edit dashboards, create alerts, and run reports
- **Viewer** — read-only access to dashboards and reports

## Connector security

When you connect external sources — Google Ads, GA4, HubSpot, Salesforce, or email platforms — Polaris uses **OAuth authentication**. We never store your login credentials; instead, we request specific, limited permissions to read your data. 

Your **auth tokens are encrypted** at rest. If a token expires, only users with Admin permissions can reconnect the source.

## Data in transit & at rest

All data transmitted to Polaris is **encrypted in transit** (TLS). Scheduled syncs (hourly or daily) pull fresh data securely from your connected sources.

## Security concerns?

If you suspect a data breach, unauthorized access, or any security issue, contact our security team immediately via support. Polaris customers on the **Enterprise plan** receive priority incident response.

---

Still stuck? [Contact support.](#contact)
