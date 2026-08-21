# ER008 — Not synced with HubSpot

Polaris shows ER008 when your HubSpot connection stops returning contacts, deals, or pipeline data, so revenue figures sourced from your CRM stop moving.

## What ER008 means for revenue and attribution

ER008 breaks the link between marketing touchpoints and revenue: campaigns keep collecting clicks, but new deals never arrive to be credited. Reports that blend ad spend with CRM revenue will understate return until ER008 clears.

The usual causes are an expired OAuth token, a HubSpot user who lost permissions, or a HubSpot account that was disconnected on their side.

## How to fix ER008 in HubSpot

1. Open **Settings > Connectors** and select the **HubSpot** connector.
2. Click **Reconnect** (Admin role required) and sign in to HubSpot.
3. Review the permissions Polaris requests — read access to contacts, deals, and company data — and approve them all. A partial approval leaves ER008 open.
4. In HubSpot, confirm the account you used still has access to the pipelines you report on.
5. Wait for the next scheduled sync and check that new deals appear.

HubSpot requires the **Growth** plan or above. If your workspace is on Starter you will see PF003 rather than ER008. If ER008 persists after a full reconnect, contact support with your HubSpot portal ID.
