# How to connect your Brevo account

Polaris syncs your Brevo email and SMS campaigns, contacts, and marketing automations. Brevo is available on **all plans** (Starter, Growth, and Enterprise) at no extra cost.

## Before you start

- You must have **Admin** role in your Polaris workspace to connect or reconnect integrations.
- You'll need a Brevo **API v3 key** (found under **SMTP & API > API Keys**).
- The Brevo user must have permissions to read Campaigns, Contacts, and SMS Campaigns.

## Steps

1. **Generate an API key in Brevo**
   In Brevo, go to **SMTP & API > API Keys**. Click **Generate a new API key**. Name it *"Polaris integration"* and copy the key.

2. **Open Polaris Connectors**
   In your Polaris workspace, go to **Settings > Connectors**.

3. **Find Brevo**
   Scroll to **Email marketing** and click **Brevo**.

4. **Paste the API key**
   Paste the Brevo API v3 key from step 1. Click **Connect**.

5. **Confirm setup**
   Polaris validates the key and begins syncing on the next scheduled sync (typically within 1 hour).

## What happens next

Email and SMS campaign performance, contact lists, and automation stats appear in your dashboards. Available for attribution alongside your other marketing channels. Syncs run every 2 hours.

## Troubleshooting

**"Invalid API key" error?**
Ensure you generated a v3 API key (not v2, which is deprecated). Regenerate in Brevo and paste the new key.

**Data not appearing?**
Check sync status under **Connectors > Sync status**. Brevo's initial backfill can take up to 4 hours for accounts with long history.

**SMS campaigns not syncing?**
Ensure SMS is enabled on your Brevo plan and that the API key has SMS scope. Contact support if the SMS module is active but data is not syncing.

Still stuck? [Contact support](mailto:support@polaris.app).
