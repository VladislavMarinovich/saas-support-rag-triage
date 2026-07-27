# Attribution models in Polaris, explained

Attribution tells you which marketing touchpoint deserves credit for a conversion. Polaris blends data from your Google Ads, GA4, email, and CRM to show you the full customer journey.

## How Polaris calculates attribution

Polaris uses **multi-touch attribution**, meaning credit is shared across all touchpoints a customer interacted with before converting. This differs from last-click (Google Ads default) or first-click models — you get a more complete picture of what actually drives revenue.

Attribution requires:

1. **GA4 connected** — tracks user interactions across your site
2. **CRM synced** (HubSpot, Salesforce) — maps interactions to deals/revenue
3. **UTM parameters on all paid ads** — so Polaris can identify which campaign, source, and medium drove the click
4. **Email platform connected** (Mailchimp, Brevo) — includes email touchpoints in the journey

## Common setup issues

**Missing UTMs?** Add `utm_source`, `utm_medium`, and `utm_campaign` to your ad links. Without them, Polaris can't attribute clicks to specific campaigns.

**GA4 or CRM not connected?** Check that your connectors are active (Admin+ only). If auth has expired, reconnect in **Workspace Settings > Connectors**.

**Seeing old data?** Attribution syncs on your workspace schedule (hourly or daily). New conversions appear in the next sync cycle.

## View your attribution

1. Go to **Dashboards** and select or create a dashboard
2. Add an **Attribution** widget
3. Choose your model and date range
4. See credit distribution across your campaigns

Still stuck? [Contact support](#).
