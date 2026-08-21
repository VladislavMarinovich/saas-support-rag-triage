# Connect Salesforce to Polaris

Salesforce is available on the **Enterprise** plan. On Starter or Growth the connector card shows PF003 instead of a **Connect** button, and starting the flow returns PL002.

## What you need before connecting Salesforce

- **Enterprise** plan on your Polaris workspace — check **Settings > Billing**
- **Admin** role in Polaris
- A Salesforce user with read access to **Accounts** and **Opportunities**, and API access enabled on its profile
- Your Salesforce org ID
- Cooperation from your Salesforce administrator if the org restricts API logins by IP range

## Connecting the Salesforce org

1. Go to **Settings > Connectors** and click **+ Add Connector**.
2. Select **Salesforce**.
3. Click **Authorize** and sign in with the Salesforce user that has the required read access.
4. Approve the OAuth permissions.
5. Confirm the connector shows **Active** and the org ID is the one you expect.

The first sync of a large org takes longer than other connectors; if it does not finish in the allowed window you will see ER004, which resolves on the next scheduled sync.

## What Salesforce data Polaris reads

Polaris reads accounts, opportunities, and their amounts and stages, so closed revenue can be attributed back to the campaigns that produced it. It never writes to Salesforce.

If Salesforce stops syncing later, the connector reports ER009 — usually a revoked session or a profile that lost object access. If your workspace is on Enterprise, the user can read Opportunities in Salesforce directly, and the connection still fails, contact support with your Salesforce org ID.
