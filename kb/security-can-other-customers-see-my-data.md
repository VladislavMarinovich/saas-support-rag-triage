# Can other customers see my data? How workspace isolation works

No. Your workspace is a separate environment, and no other Polaris customer can reach your dashboards, connectors, or metrics — this article explains the mechanism, so you can verify the claim rather than take it on faith.

## Why another company cannot reach your numbers

Polaris is multi-tenant: many customers share the service, but each workspace is logically isolated from every other one. A user belongs to a single workspace and every request is scoped to it, so there is no path — accidental or deliberate — from one customer's session to another customer's data.

Inside your own workspace, access is controlled by role: Admins manage connectors and users, Analysts build dashboards and alerts, Viewers read what is shared with them. Someone outside your workspace has no role in it at all, which is why they see nothing.

If you are asking because you share an agency or a parent company with another team: separate workspaces cannot see each other's data. Use one workspace with roles if the teams need shared dashboards.

## How your credentials and data are protected

- **We never store your provider passwords.** Connectors use OAuth, so Polaris holds a scoped token, not your login. Tokens are encrypted at rest, and only Admins can reconnect a source (PF005).
- **Read-only access.** Polaris reads from Google Ads, Meta Ads, Google Analytics, HubSpot, Salesforce, and Mailchimp; it never writes back — no budget, campaign, or CRM record is modified.
- **Encrypted in transit.** All traffic to Polaris uses TLS, including scheduled syncs.
- **The assistant cannot read your workspace.** Ask it about your own numbers and it returns AG003 by design, so your metrics are never sent to a language model.

If you suspect unauthorized access or any security issue, contact support and say so explicitly — security reports are routed to our security team immediately, and Enterprise workspaces receive priority incident response. Do not wait for the assistant, which returns AG004 for security matters.
