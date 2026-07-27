# Why your data looks stale: sync schedules and delays

Polaris syncs your marketing and revenue data on a regular schedule — typically hourly or daily, depending on your plan. If your dashboards and metrics look out of date, here are the most common causes and how to fix them.

## Most common issues

**1. Your last sync hasn't completed yet**
Data freshness depends on your sync window. Check the **Connectors** page to see when your next sync is scheduled and the timestamp of your most recent successful sync.

**2. A connector is disconnected or authentication expired**
OAuth tokens from Google Ads, GA4, HubSpot, Salesforce, Mailchimp, or Brevo can expire. 
- Go to **Connectors** and look for any red error badges.
- If you see an expired auth warning, you'll need to **reconnect**. (Note: only workspace Admins can reconnect connectors.)
- Click **Reconnect**, re-authenticate with the source platform, and the next scheduled sync will pull fresh data.

**3. A sync failed silently**
If a connector shows a failed sync status, the data won't update until the next scheduled attempt. Check for any error messages on the Connectors page. If it persists, contact support.

**4. Your plan's sync frequency is limited**
Starter plans sync less frequently than Growth or Enterprise. If you need fresher data, consider upgrading your plan.

## What to do next

- Verify all your connectors are connected and showing green status.
- Check the timestamp of the last successful sync.
- Wait for the next scheduled sync window.

Still stuck? [Contact support.](#)
