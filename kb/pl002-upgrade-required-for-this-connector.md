# PL002 — Upgrade required for this connector

Polaris shows PL002 when you start connecting a source that needs a higher plan than the one your workspace is on, and the flow stops at the authorization step.

## What PL002 means mid-setup

PL002 appears after you begin — sometimes after you have already signed in at the provider — because the plan check runs before Polaris stores the connection. Nothing is left half-connected: no data is pulled and no token is kept.

You will meet PL002 most often with **HubSpot** or **Mailchimp** on a Starter workspace, and with **Salesforce** on Starter or Growth.

## How to complete the setup after PL002

1. Note which connector triggered PL002.
2. Ask an **Admin** to open **Settings > Billing** and select the plan that includes it: Growth for HubSpot and Mailchimp, Enterprise for Salesforce.
3. Confirm the plan change — it applies immediately, and syncs on existing connectors are unaffected.
4. Return to **Settings > Connectors** and run the connection again from the start.

If you would rather not change plans, Google Ads, Meta Ads, Google Analytics, and Slack are available on every plan. If your plan already covers the connector and PL002 still stops the flow, contact support with the connector name.
