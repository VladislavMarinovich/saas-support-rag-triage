# ER001 — Authorization expired

Polaris raises ER001 when the OAuth token for one of your connectors has expired and the platform stopped accepting our data requests. Nothing is broken on your side — tokens expire on a schedule set by the provider.

## What ER001 means for your data

ER001 is an authorization error, not a sync error: Polaris never reached your data because the token was rejected. While ER001 is open, dashboards, alerts, and reports keep showing the last values pulled before the token expired, so numbers look frozen rather than empty.

You will see ER001 on the connector card in **Settings > Connectors**, and in any report or alert that depends on that source.

## How to clear ER001 by reauthorizing the connector

Reauthorizing (also called reconnecting or rotating the token) takes under a minute, and only an **Admin** can do it:

1. Open **Settings > Connectors** and find the connector flagged with ER001.
2. Click **Reconnect**.
3. Sign in on the provider's login screen with the account that owns the data source.
4. Approve the permissions Polaris requests.
5. Confirm the connector status changes to **Active**.

Data resumes on the next scheduled sync — within the hour for hourly syncs, next day for daily. If ER001 comes back within a few days of reauthorizing, the provider account may have revoked access; contact support with your workspace name and the connector name.
