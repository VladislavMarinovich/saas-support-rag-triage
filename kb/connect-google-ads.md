# Connect Google Ads to Polaris

Google Ads is included on **every plan** — Starter, Growth, and Enterprise — so you can connect it as soon as your workspace exists. This guide covers the connection itself; spend and conversion data appears in your dashboards after the first sync.

## What you need before connecting Google Ads

- **Admin** role in your Polaris workspace (only Admins can add connectors)
- A Google account with at least read access to the Google Ads account you want to report on
- The Google Ads account ID, so you can confirm you linked the right one
- A free connection slot on your plan — if you have none, you will see PL001

## Connecting the Google Ads account

1. Go to **Settings > Connectors** and click **+ Add Connector**.
2. Select **Google Ads**.
3. Click **Authorize** and sign in with the Google account that has access.
4. Approve the read-only permissions Polaris requests.
5. Choose the Google Ads account from the list and click **Confirm**.
6. Check the connector card shows **Active** and note the account ID.

The first sync can take up to an hour. Once it completes, Google Ads spend, clicks, and conversions are available for dashboards, alerts, and attribution.

## What Google Ads data Polaris reads

Polaris reads campaign, ad group, and conversion performance — enough to blend paid spend with the revenue coming from your CRM. It never writes to Google Ads: no budget, bid, or campaign is ever changed from Polaris.

If Google Ads stops updating later, the connector reports ER005; an expired login reports ER001. Both are fixed with **Reconnect** from the same card. If authorization fails repeatedly with an account that works in Google Ads directly, contact support with the Google Ads account ID.
