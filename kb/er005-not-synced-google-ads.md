# ER005 — Not synced with Google Ads

Polaris shows ER005 when your Google Ads connection stops returning data, so spend, clicks, and conversion numbers from Google Ads stay stuck at their last synced values.

## What ER005 means for your Google Ads numbers

ER005 is specific to the Google Ads connector. Other sources keep syncing normally, which is why a dashboard can show fresh GA4 sessions next to Google Ads spend that has not moved since yesterday.

While ER005 is open you will notice:

- Google Ads widgets showing the same totals across several refreshes
- Attribution reports crediting fewer paid conversions than expected
- Alerts on Google Ads metrics not firing, because no new data crosses the threshold

ER005 does not delete history. Everything pulled before the error stays available.

## How to fix ER005 in Google Ads

1. Open **Settings > Connectors** and select the **Google Ads** connector.
2. Check what the card reports next to ER005: an expired authorization, revoked access, or a failed sync.
3. If it asks for authorization, click **Reconnect** and sign in with the Google account that has access to the Google Ads account. Only an **Admin** can reconnect.
4. In Google Ads, confirm that account still has at least read access to the ad account, and that the ad account is not suspended — a suspended account returns no data and keeps ER005 open.
5. Verify the Google Ads account ID on the connector card matches the account you expect. ER005 also appears when the linked ad account was closed or replaced.
6. Save and wait for the next scheduled sync. Google Ads data reappears within the hour on hourly syncs.

Google Ads is available on every plan, so ER005 is never caused by your plan. If ER005 is still there after reconnecting with an account that has access, contact support with your workspace name and the Google Ads account ID.
