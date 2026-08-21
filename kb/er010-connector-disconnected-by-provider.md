# ER010 — Connector disconnected by provider

Polaris raises ER010 when the data provider itself terminated the connection: someone revoked Polaris in the provider's app settings, the account was closed, or the provider disabled third-party access.

## Why ER010 is not the same as an expired token

An expired token (ER001) is routine and clears with a reconnect. ER010 means the provider deliberately dropped the integration, so reconnecting will fail until the access is granted again on their side. Polaris stops retrying after ER010 to avoid lockouts, so the connector stays inactive until someone acts.

Look for ER010 after a security review, an offboarding, or a change of agency access.

## How to restore a connection after ER010

1. In the provider (Google Ads, Meta Ads, Google Analytics, HubSpot, Salesforce, Mailchimp, Slack), open the connected-apps or integrations settings and check whether Polaris is still authorized.
2. If Polaris was removed, grant access again, or use a different account that has it.
3. Confirm the underlying account is active — a closed ad account or a cancelled CRM subscription keeps ER010 open.
4. In Polaris, open **Settings > Connectors** and click **Reconnect** (Admin role required).
5. Verify the status changes to **Active** and wait for the next scheduled sync.

If the provider shows Polaris as authorized and ER010 still appears, contact support with the connector name and the time access was restored.
