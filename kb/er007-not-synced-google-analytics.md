# ER007 — Not synced with Google Analytics

Polaris shows ER007 when your Google Analytics connection stops returning data, so sessions, users, and web conversions stop updating in your dashboards.

## What ER007 means for your web analytics

ER007 is specific to the Google Analytics connector. Attribution is the first place people notice it: without fresh Google Analytics data, Polaris cannot map new clicks to campaigns, so recent conversions appear unattributed.

Common causes are an expired Google authorization, a property that was deleted or recreated, or a data stream that was switched.

## How to fix ER007 in Google Analytics

1. Open **Settings > Connectors** and select the **Google Analytics** connector.
2. Click **Reconnect** (Admin role required) and sign in with a Google account that has at least Viewer access to the property.
3. Confirm the property and data stream on the connector card still match the ones you report on. If the property was recreated, select the new one — a recreated property has a different ID even with the same name.
4. Wait for the next scheduled sync; Google Analytics data syncs hourly.

Google Analytics is available on every plan. If ER007 stays open after reconnecting with an account that can see the property in Google Analytics directly, contact support with the property ID.
