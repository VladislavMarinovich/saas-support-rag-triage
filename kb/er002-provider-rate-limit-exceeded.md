# ER002 — Provider rate limit exceeded

Polaris raises ER002 when a data provider (Google Ads, Meta Ads, Google Analytics, HubSpot, Salesforce) temporarily refuses new requests because too many were made in a short window. It is a throttle on their side, not a failure of your connection.

## What ER002 means and why it clears on its own

ER002 is temporary by design. Your credentials are valid and your connector stays **Active**; only the current sync was cut short. The provider's quota resets on its own schedule — usually within an hour — and the next scheduled sync picks up the data that was skipped.

You are more likely to see ER002 if several people trigger manual syncs at once, or if the same provider account is also feeding other tools.

## How to handle ER002 without breaking anything

1. **Wait for the next scheduled sync.** In most cases ER002 disappears with no action.
2. **Avoid manual syncs while ER002 is open** — each retry counts against the same quota and can extend the throttle.
3. **Check whether the numbers you need are already there.** ER002 skips new rows; it does not delete existing data.
4. **Stagger heavy work.** If you regularly export large date ranges, run them outside your usual sync window.

If ER002 repeats for more than a day, or you see it on every sync of the same source, contact support with the connector name and the times you saw the error — the provider account may need a higher quota.
