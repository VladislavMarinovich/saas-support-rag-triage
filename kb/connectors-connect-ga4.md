# How to connect Google Analytics 4

Connect your Google Analytics 4 property to Polaris to unify your web traffic data with marketing and revenue metrics.

## Requirements

- **Admin role** in your Polaris workspace (only Admins can add connectors)
- Active Google Analytics 4 property
- Google account with access to that property

## Steps

1. In Polaris, go to **Connectors** → **+ Add Connector**.

2. Select **Google Analytics 4** from the list.

3. Click **Authorize**. You'll be redirected to Google's login page.

4. Sign in with the Google account that has access to your GA4 property.

5. Review the permissions prompt and click **Allow**. Polaris requests read-only access to your GA4 data.

6. You'll return to Polaris. Select your **GA4 property** from the dropdown menu.

7. Click **Confirm**. The connector is now active.

Polaris will begin syncing your GA4 data on the next scheduled sync (usually within the hour). Data appears in your dashboards and attribution models once the sync completes.

## Troubleshooting

**"Authorization failed"**  
Make sure you're signing in with a Google account that has Editor or Viewer access to the GA4 property.

**"Property not showing in the dropdown"**  
Refresh the page. If it still doesn't appear, the account may not have access to that property—verify in Google Analytics directly.

**Data hasn't synced yet**  
Initial syncs can take up to 1 hour. Check back later, or contact support to check sync status.

---

Still stuck? [Contact support](mailto:support@polaris.com).
