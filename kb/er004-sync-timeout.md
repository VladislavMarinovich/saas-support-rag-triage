# ER004 — Sync timeout

Polaris raises ER004 when a sync starts normally but the provider does not finish returning data within the allowed window. The connection is fine; the request was simply too slow or too large to complete.

## What ER004 means for the data already pulled

ER004 leaves partial data in place: rows that arrived before the timeout are kept, and the rest are retried on the next scheduled sync. That is why a dashboard can look half-updated after ER004 — some campaigns or deals show fresh numbers while others lag by a cycle.

Large accounts, long date ranges, and first-time syncs are the most common triggers, because the initial pull is much bigger than a routine incremental one.

## How to resolve ER004 and prevent repeats

1. **Let the next scheduled sync run.** Most ER004 cases resolve without action once the backlog is smaller.
2. **Check the provider's status page** if ER004 appears across several connectors at once — a slow provider affects all of them.
3. **Narrow what you pull.** If ER004 happens on every sync of one source, reduce the date range on the dashboards and reports that depend on it.
4. **Re-run a first-time sync out of hours.** Initial imports finish faster when the provider is less busy.

If ER004 repeats on three consecutive syncs of the same connector, contact support with the connector name and the sync times — we can check the delivery logs on our side.
