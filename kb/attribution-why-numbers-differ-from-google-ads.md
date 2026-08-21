# Why Polaris and Google Ads report different conversion numbers

Comparing conversions in Polaris against the Google Ads or Meta Ads interface almost always shows a gap. In most cases both numbers are correct — they are answering different questions.

## The four reasons the totals differ

1. **Different attribution models.** Google Ads credits the click it considers responsible; Meta credits its own view- and click-through windows. Polaris uses **multi-touch attribution**, spreading credit across every touchpoint in the journey. A conversion Google Ads counts as one of its own may be shared with an email and an organic visit in Polaris.
2. **Different attribution windows.** Each platform counts conversions back to the click within its own window, so a late conversion may land in a different period in each tool.
3. **Sync timing.** Polaris reports as of the last successful sync (hourly or daily by plan). The platform's own interface is live, so today's partial numbers will always look lower in Polaris until the next sync — that is DB003, not a discrepancy.
4. **Missing UTMs.** A paid click without `utm_source`, `utm_medium`, and `utm_campaign` reaches your site but cannot be tied to the campaign, so Polaris attributes it elsewhere while the platform still counts it.

## How to reconcile the numbers

1. Match the date ranges exactly, and allow for the platform's attribution window before comparing recent days.
2. Confirm the sync timestamp in **Settings > Connectors** — comparing a live platform total against a six-hour-old sync is not a like-for-like comparison.
3. Check that your paid links carry all three UTM parameters; add them where they are missing and expect improvement only for traffic that arrives afterwards.
4. Compare a closed period — last full month — rather than the current week, so windows and syncs have settled.
5. Expect a residual difference. Multi-touch will not equal last-click, and should not.

Use the platform's numbers for platform-level decisions (bids, budgets) and Polaris for cross-channel comparisons. If Polaris shows dramatically fewer conversions than the platform for a closed period with UTMs in place, contact support with the campaign name and dates.
