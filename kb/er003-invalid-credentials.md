# ER003 — Invalid credentials

Polaris raises ER003 when the account used to connect a data source no longer has valid access: the password changed, the user was removed from the provider account, or the permission that Polaris relies on was revoked.

## How ER003 differs from an expired token

ER003 and ER001 look similar on the connector card but have different fixes. ER001 means the token aged out and simply needs reauthorizing. ER003 means the credentials themselves are no longer accepted — reauthorizing with the same account will fail again until access is restored on the provider side.

A quick way to tell them apart: if the person who originally connected the source has left the company or lost access, it is almost always ER003.

## How to fix ER003 in the provider account

1. Identify which account connected the source — the connector card in **Settings > Connectors** shows it.
2. In the provider (Google Ads, Meta Ads, Google Analytics, HubSpot, Salesforce, Mailchimp), confirm that account still exists and still has at least read access to the property, ad account, or CRM data.
3. If access is gone, either restore it, or reconnect Polaris using an account that has it.
4. Back in Polaris, click **Reconnect** on the connector (Admin role required) and sign in with the working account.

If the credentials are definitely valid and ER003 persists after two reconnect attempts, contact support with the connector name and the account used.
