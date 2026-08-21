# Connect Mailchimp to Polaris

Mailchimp is available on the **Growth** and **Enterprise** plans, as part of email marketing support. On Starter the connector card shows PF003.

## What you need before connecting Mailchimp

- **Growth** plan or above — check **Settings > Billing**
- **Admin** role in Polaris
- A Mailchimp login with access to the audience and campaign data you report on
- A free connection slot (otherwise PL001)

## Connecting the Mailchimp account

1. Go to **Settings > Connectors** and click **+ Add Connector**.
2. Select **Mailchimp**.
3. Click **Authorize** and sign in to Mailchimp.
4. Approve the read permissions Polaris requests.
5. Confirm the connector shows **Active**.

## What Mailchimp data Polaris reads, and why it matters for attribution

Polaris reads campaign sends, opens, clicks, and the audience metadata needed to tie them to your other sources. Adding Mailchimp puts email touchpoints into multi-touch attribution — without it, a customer who clicked an email before converting looks like they arrived from another channel entirely.

Email links still need UTM parameters for campaign-level attribution: the connector explains *that* an email was opened and clicked, while the UTMs explain *which* campaign the click belongs to.

If Mailchimp stops syncing, the connector reports ER001 for an expired login or ER003 if the account lost access. If you are on Growth or Enterprise and the connector still shows PF003, contact support with your workspace name.
