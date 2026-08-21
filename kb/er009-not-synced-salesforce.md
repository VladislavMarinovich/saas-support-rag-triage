# ER009 — Not synced with Salesforce

Polaris shows ER009 when your Salesforce connection stops returning opportunity and account data, so CRM revenue in your dashboards stops updating.

## What ER009 means for your Salesforce data

ER009 is specific to the Salesforce connector, which is available on the **Enterprise** plan. It usually points to one of three things: the OAuth session was revoked, the connected user lost access to the objects Polaris reads, or a Salesforce security setting now blocks the connection.

Existing opportunity history stays in Polaris while ER009 is open; only new and changed records are missing.

## How to fix ER009 in Salesforce

1. Open **Settings > Connectors** and select the **Salesforce** connector.
2. Click **Reconnect** (Admin role required) and sign in with a Salesforce user that can read Accounts and Opportunities.
3. In Salesforce, confirm that user's profile still grants read access to those objects and that API access is enabled for the profile.
4. If your Salesforce org restricts logins by IP range or requires a security token for API access, ask your Salesforce administrator to allow the connection.
5. Wait for the next scheduled sync and confirm new opportunities appear.

If your workspace is not on Enterprise, Salesforce is not available and you will see PF003 instead. If ER009 continues after reconnecting with a user who can read those objects, contact support with your Salesforce org ID.
