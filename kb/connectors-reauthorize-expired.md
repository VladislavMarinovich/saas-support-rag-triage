# Reconnecting an expired connector

OAuth tokens from your connected platforms (Google Ads, GA4, HubSpot, Mailchimp, Brevo, Salesforce) expire periodically. When this happens, Polaris can't sync new data until you reconnect.

## Signs your connector has expired

- Data stopped updating at its usual schedule (hourly or daily)
- You see a warning badge on the connector in **Settings > Connectors**
- Recent dashboards or reports show stale numbers

## How to reconnect

**Only Admins can reconnect connectors.** If you're an Analyst or Viewer, ask your workspace Admin to complete these steps.

**As an Admin:**

1. Go to **Settings > Connectors**
2. Find the expired connector (Google Ads, GA4, etc.)
3. Click **Reconnect**
4. You'll be redirected to the platform's login screen—sign in with the account that owns the data source
5. Grant Polaris permission to access your data
6. Return to Polaris; the connector status will update to "Active"

Syncing resumes on the next scheduled cycle (within 1 hour for hourly syncs; next day for daily syncs).

## Why only Admins can reconnect

Reconnecting requires OAuth permissions that only Admin-level roles hold in your workspace. This protects your data source credentials and prevents accidental disconnections.

## Still stuck?

If the connector remains inactive after reconnecting, or you're unsure which account to use, [contact support](mailto:support@polaris.com).
