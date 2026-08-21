# A campaign shows no data: fixing missing or wrong UTMs

When a campaign appears in your ad platform but not in Polaris attribution reports, the cause is almost always the UTM tags on its links rather than the connector.

## Why a live campaign can be invisible in attribution

Polaris identifies campaigns by the UTM parameters on the link a person clicked. Without them, the visit still arrives — but with nothing that ties it to a campaign, so it is attributed elsewhere and the campaign looks like it produced nothing.

The usual culprits, in the order you should check them:

- **No UTMs at all** on the ad's destination URL
- **Inconsistent values** — `Google` in one ad and `google` in another creates two sources that never add up
- **A renamed campaign** in the platform while the old `utm_campaign` value stays in the links
- **UTMs added after the traffic ran** — tracking only sees data from the moment it is in place, never retroactively
- **A stale sync**, if Google Analytics is behind (ER007 or DB003)

## Fixing the tags and confirming the fix

1. Open the ad's destination URL and confirm it carries `utm_source`, `utm_medium`, and `utm_campaign`.
2. Standardize the values: lowercase, consistent, and descriptive — `utm_source=google`, `utm_medium=cpc`, `utm_campaign=summer_sale`.
3. Apply the same convention to every ad in the campaign; one untagged ad leaves a permanent gap.
4. Confirm Google Analytics is connected and syncing in **Settings > Connectors** — attribution needs it, and ER007 stops it.
5. Wait for the next sync, then check the campaign appears in your attribution report.
6. Accept that clicks from before the fix stay unattributed. Note the date you corrected the tags so you can explain the step change to your team.

If the links carry correct UTMs, Google Analytics synced after they went live, and the campaign is still absent, contact support with the campaign name and one example destination URL.
