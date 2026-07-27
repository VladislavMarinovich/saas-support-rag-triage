# A scheduled report didn't arrive

Scheduled reports should arrive at your inbox on the set cadence. If you're missing one, try these checks in order.

## 1. Verify the recipient email address

The most common cause is a typo or outdated email in the report configuration.

1. Go to **Reports** in your workspace.
2. Click the report name to open settings.
3. Check the **recipient email(s)** field. Correct any errors.
4. Re-save and allow 5–10 minutes for the next scheduled run.

## 2. Check your spam / promotions folder

Reports are sent from `reports@polaris.io`. If you don't see the email in your inbox, check spam, promotions, or other filtered folders. Add `reports@polaris.io` to your contacts to whitelist future messages.

## 3. Confirm the report schedule is active

1. Open the report settings.
2. Verify the **schedule** is enabled (toggle should be on).
3. Check the **frequency** and **next run time** — is it in the past, or has it not reached the next scheduled slot yet?

## 4. Check data freshness

If the report contains data from a connected source (Google Ads, GA4, HubSpot, etc.), a sync delay may pause report generation.

1. Go to **Connectors**.
2. Verify each source shows a recent **last sync** timestamp.
3. If a sync failed, you may need **Admin** role to reconnect.

## Still stuck?

[Contact support](https://polaris.io/support) with your workspace name and report ID, and we'll investigate the delivery logs.
