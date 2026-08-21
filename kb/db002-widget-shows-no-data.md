# DB002 — Widget shows no data

Polaris shows DB002 on a single widget that resolved correctly but has nothing to display for the selected period.

## Why one widget is empty while the rest of the dashboard works

DB002 means the query succeeded and returned zero rows. That is a data question, not a failure:

- The date range predates the connection, so no data was ever collected for it
- A filter or breakdown excludes everything (a campaign name that no longer exists, a segment with no members)
- The source synced but genuinely had no activity in that window
- The requested range is older than your plan's retention window (see PL005)

Because the dashboard itself loads, DB002 is different from DB001, and because the query ran, it is different from a permission block (PF001).

## How to resolve DB002

1. Widen the date range and see whether numbers appear — that isolates a range problem instantly.
2. Clear filters and breakdowns on the widget, then reapply them one at a time.
3. Confirm the source's last successful sync in **Settings > Connectors**; a connection added yesterday cannot show last month.
4. Compare against the same metric in the provider's own interface to confirm activity actually existed.

If the provider shows activity for a range inside your retention window and the widget stays empty, contact support with the dashboard name and the widget's metric.
