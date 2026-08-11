# How to connect your Google Ads account

Polaris syncs your Google Ads campaigns, ad groups, and cost data to unify them with your analytics and conversion data. Google Ads is available on **all plans** (Starter, Growth, and Enterprise) at no extra cost.

## Before you start

- You must have **Admin** role in your Polaris workspace to connect or reconnect integrations.
- You'll need Google Ads login credentials with **Admin** or **Standard** access to the account.
- If you use a Manager (MCC) account, you can connect the manager and select which sub-accounts to sync.

## Steps

1. **Open Connectors**
   From your workspace, go to **Settings > Connectors**.

2. **Find Google Ads**
   Scroll to **Ad platforms** and click **Google Ads**.

3. **Authorize Polaris**
   Click **Connect**. You'll be redirected to Google's OAuth consent screen.

4. **Sign in to Google**
   Choose the Google account associated with your Google Ads. Review the permissions Polaris requests (read access to campaigns, metrics, and cost data).

5. **Approve the connection**
   Click **Allow**. You'll return to Polaris.

6. **Select accounts**
   If you have multiple Google Ads accounts under a Manager, choose the ones to sync. Otherwise the single account is auto-selected.

7. **Confirm setup**
   Your Google Ads account is now connected. Polaris will begin syncing daily performance data on the next scheduled sync (typically within 1 hour).

## What happens next

Cost, clicks, impressions, and campaign data from Google Ads appear in your dashboards and become available for attribution alongside your analytics conversions. Syncs run hourly on Growth and Enterprise plans, daily on Starter.

## Troubleshooting

**Connection failed?**
Ensure the Google account you signed in with has direct access to the Google Ads account (not just delegated via email). If you use 2FA, complete the additional prompt.

**Data not appearing?**
Check that the sync has completed under **Connectors > Sync status**. Google Ads' initial backfill can take up to 2 hours for accounts with long history. If data is still missing after 4 hours, contact support.

**"Developer token" error?**
Contact support — this rare error requires Polaris to whitelist your Manager account.

Still stuck? [Contact support](mailto:support@polaris.app).
