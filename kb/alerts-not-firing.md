# My alert isn't firing

Alerts in Polaris trigger when your connected data meets the threshold you've set. If yours isn't firing, check these common causes:

## 1. Threshold is set too high or low
Your alert threshold may not match your actual data. 
- Open the alert and review the condition (e.g., "trigger when conversions > 50").
- Check your dashboard to see the current metric value.
- Adjust the threshold if needed. Save and monitor for the next sync cycle.

## 2. Your connector hasn't synced recently
Polaris pulls data on a schedule (hourly or daily, depending on your plan). If your connector is stale or broken, the alert won't fire.
- Go to **Connectors** and check the sync status of the data source (Google Ads, GA4, HubSpot, etc.).
- If the last sync was more than a few hours ago, manually trigger a sync or wait for the next scheduled sync.
- If a connector shows an error (e.g., "auth expired"), an Admin will need to reconnect it.

## 3. You don't have permission to receive alerts
Alerts respect your workspace role (Admin, Analyst, Viewer). If you're a Viewer, you may not receive notifications.
- Ask your Admin to verify your role in **Users & Workspace**.
- Check your alert recipient email address in the alert settings.

## 4. Alert is paused or misconfigured
Confirm the alert is active and the notification email is correct.
- Open the alert and ensure it's toggled **on**.
- Double-check the recipient email address for typos.

Still stuck? [Contact support](#).
