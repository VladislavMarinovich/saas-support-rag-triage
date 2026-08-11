# How to connect your Zoho CRM

Polaris syncs your Zoho CRM leads, contacts, and deals. Zoho CRM is available on the **Enterprise** plan.

## Before you start

- You must have **Admin** role in your Polaris workspace to connect or reconnect integrations.
- You must be on the **Enterprise plan** in Polaris. If you're on Starter or Growth, upgrade first or contact our team.
- You'll need a Zoho CRM user with **Administrator** or a custom profile that allows OAuth access to Leads, Contacts, and Deals modules.
- Confirm your **Zoho data center region** (US, EU, IN, AU, or CN). This affects the OAuth flow.

## Steps

1. **Open Connectors**
   From your workspace, go to **Settings > Connectors**.

2. **Find Zoho CRM**
   Scroll to **CRM integrations** and click **Zoho CRM**.

3. **Select your data center**
   Choose your Zoho region (US, EU, IN, AU, or CN). This must match your Zoho account's location.

4. **Authorize Polaris**
   Click **Connect**. You'll be redirected to Zoho's login page.

5. **Sign in to Zoho**
   Enter your Zoho credentials.

6. **Approve the permissions**
   Review the permissions Polaris requests (read access to Leads, Contacts, Deals, and Modules). Click **Accept**.

7. **Confirm setup**
   Your Zoho CRM is now connected. Polaris will begin syncing on the next scheduled sync (typically within 1 hour).

## What happens next

Leads, contacts, and deals from Zoho appear in your dashboards and are available for attribution and pipeline analysis. Syncs run hourly on Enterprise plans.

## Troubleshooting

**Connection failed?**
Verify you selected the correct data center region. The wrong region will silently fail OAuth. Also confirm your Zoho user has API access enabled in **Setup > Users & Control > User Roles**.

**Data not appearing?**
Check that the modules (Leads, Contacts, Deals) are enabled for API access in Zoho. Also check sync status under **Connectors > Sync status**.

**"Rate limit exceeded" error?**
Zoho enforces API rate limits per plan. If you hit them, contact your Zoho admin to increase the daily API credit or upgrade your Zoho plan.

Still stuck? [Contact support](mailto:support@polaris.app).
