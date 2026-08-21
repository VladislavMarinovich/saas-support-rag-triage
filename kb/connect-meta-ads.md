# Connect Meta Ads to Polaris

Meta Ads — Facebook and Instagram advertising — is included on **every plan**: Starter, Growth, and Enterprise. Connecting it brings social spend and results next to your search and CRM data.

## What you need before connecting Meta Ads

- **Admin** role in Polaris
- A Facebook account with access to the ad account through Business Manager
- The Meta ad account ID
- A free connection slot on your plan (otherwise you will see PL001)

## Connecting the Meta Ads account

1. Go to **Settings > Connectors** and click **+ Add Connector**.
2. Select **Meta Ads**.
3. Click **Authorize** and sign in with Facebook.
4. When Meta asks which assets to share, **select the ad account you report on**. This is the step people miss — an authorization without the ad account selected produces a connector that never returns data.
5. Approve the permissions and return to Polaris.
6. Confirm the connector shows **Active** and the ad account ID matches.

Meta Ads syncs on your workspace schedule, hourly or daily depending on your plan.

## What Meta Ads data Polaris reads

Polaris reads campaign, ad set, and ad performance: spend, impressions, clicks, and the conversions Meta reports. It is read-only — no campaign or budget in Meta is ever modified from Polaris.

Note that Meta and Polaris may report different conversion counts, because Meta attributes on its own model while Polaris uses multi-touch attribution across all your sources. If Meta data stops arriving, the connector reports ER006. If the ad account is missing from the list during authorization, ask your Business Manager admin to grant access first, then contact support with the ad account ID if it still does not appear.
