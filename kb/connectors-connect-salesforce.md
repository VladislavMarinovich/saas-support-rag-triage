# How to connect your Salesforce CRM

Polaris syncs your Salesforce accounts, opportunities, and contacts to unify them with your marketing metrics. Salesforce is available on the **Enterprise** plan.

## Before you start

- You must have **Admin** role in your Polaris workspace to connect or reconnect integrations.
- You must be on the **Enterprise plan** in Polaris. If you're on Starter or Growth, upgrade first or contact our team about unlocking Salesforce.
- You'll need a Salesforce user with **System Administrator** or **API Enabled** permissions to authorize OAuth access.

## Steps

1. **Open Connectors**
   From your workspace, go to **Settings > Connectors**.

2. **Find Salesforce**
   Scroll to **CRM integrations** and click **Salesforce**.

3. **Authorize Polaris**
   Click **Connect**. You'll be taken to Salesforce's login page.

4. **Sign in to Salesforce**
   Enter your Salesforce credentials. Choose the correct environment (Production or Sandbox).

5. **Approve the permissions**
   Review the permissions Polaris requests: read access to Accounts, Contacts, Opportunities, and standard reporting objects. Click **Allow**.

6. **Confirm setup**
   Your Salesforce org is now connected. Polaris will begin syncing on the next scheduled sync (typically within 1 hour).

## What happens next

Data from Salesforce appears in your dashboards and is available for attribution, pipeline analysis, and blending with your ad and analytics data. Syncs run hourly on Enterprise plans.

## Troubleshooting

**Connection failed?**
Ensure you're using a Salesforce user with API access enabled. If your org has IP restrictions, whitelist Polaris's egress IPs (see **Settings > Connectors > Security**).

**Data not appearing?**
Check that the sync has completed under **Connectors > Sync status**. Salesforce's initial full sync can take up to 4 hours for large orgs. If data is still missing after 6 hours, contact support.

**"Insufficient privileges" error?**
Ask your Salesforce Admin to grant the connecting user the "API Enabled" permission and re-authorize.

Still stuck? [Contact support](mailto:support@polaris.app).
