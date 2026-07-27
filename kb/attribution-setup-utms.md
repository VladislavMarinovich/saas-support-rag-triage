# Setting up UTMs and GA4 for accurate attribution

Polaris attribution relies on two foundations: **UTM parameters** in your marketing links and **GA4 data** flowing into your workspace. Without both, Polaris cannot accurately trace revenue back to campaigns.

## Step 1: Add UTM parameters to your marketing links

UTM parameters tag every link you share (ads, emails, social). Polaris reads these to identify the source, medium, and campaign.

Use this format:
```
https://yoursite.com?utm_source=google&utm_medium=cpc&utm_campaign=summer_sale
```

**Required parameters:**
- `utm_source` — where the click came from (e.g., google, facebook, email)
- `utm_medium` — the channel type (e.g., cpc, social, email)
- `utm_campaign` — your campaign name

**Best practice:** Keep parameter values lowercase, consistent, and descriptive.

## Step 2: Connect GA4 to Polaris

1. In **Workspace Settings** → **Connectors**, click **Add Connector**.
2. Select **Google Analytics 4**.
3. Authorize Polaris to read your GA4 property (requires Admin or Editor access in GA4).
4. Select the property and data stream.
5. Save. Polaris syncs GA4 data hourly.

## Step 3: Verify the connection

Once synced, navigate to **Attribution** and check that:
- Campaign names appear in your reports
- UTM source/medium/campaign values match your links
- Revenue is attributed to campaigns

If numbers look wrong, confirm UTMs were live *before* the traffic arrived — GA4 can only see data from the moment tracking began.

---

**Still stuck?** [Contact support](mailto:support@polaris.io) or check your GA4 documentation for UTM best practices.
