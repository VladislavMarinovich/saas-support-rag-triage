# How to connect your Klaviyo account

Polaris syncs your Klaviyo email campaigns, flows, and subscriber events. Klaviyo is a **paid add-on** available on any plan.

## Before you start

- You must have **Admin** role in your Polaris workspace to connect or reconnect integrations.
- The **Klaviyo add-on** must be active on your workspace. Enable it under **Settings > Billing > Add-ons**.
- You'll need a Klaviyo **Private API Key** with read access to Campaigns, Flows, and Metrics scopes.

## Steps

1. **Generate a Private API Key in Klaviyo**
   In Klaviyo, go to **Settings > API Keys > Create Private API Key**. Give it a name like *"Polaris integration"*. Under scopes, grant **Read** access to Campaigns, Flows, Metrics, Profiles, and Segments.

2. **Copy the key**
   Klaviyo shows the key only once. Copy it now.

3. **Open Polaris Connectors**
   In your Polaris workspace, go to **Settings > Connectors**.

4. **Find Klaviyo**
   Scroll to **Email marketing** and click **Klaviyo**.

5. **Paste the API Key**
   Paste the Private API Key from step 2. Click **Connect**.

6. **Confirm setup**
   Polaris validates the key and begins syncing on the next scheduled sync (typically within 1 hour).

## What happens next

Email campaign performance (opens, clicks, revenue), flows, and subscriber events appear in your dashboards. Available for attribution alongside your other channels. Syncs run every 2 hours.

## Troubleshooting

**"Invalid API key" error?**
Regenerate a new Private API Key in Klaviyo with the correct scopes (Read access to Campaigns, Flows, Metrics). Paste it in Polaris and reconnect.

**Data not appearing?**
Check that the API Key has the required scopes. Also verify sync status under **Connectors > Sync status**. Klaviyo's initial backfill can take up to 6 hours for accounts with large history.

**Revenue attribution missing?**
Ensure the Klaviyo events include the `Placed Order` metric with revenue data. Contact support to configure custom event mappings.

Still stuck? [Contact support](mailto:support@polaris.app).
