# DB003 — Data freshness delayed

Polaris shows DB003 when the data behind a dashboard is older than your sync schedule promises, so numbers are real but stale.

## How to read the DB003 warning

DB003 compares the last successful sync against your expected cadence — hourly or daily, depending on your plan. It appears when that gap grows, and it names the source that is behind rather than the widget.

Data shown under DB003 is accurate as of the timestamp on the dashboard; it is simply not current. Nothing is lost, and no action is needed if the source recovers on its next cycle.

## How to clear DB003

1. Check the freshness timestamp on the dashboard and note which source it names.
2. Open **Settings > Connectors** and look for an error on that source — ER001, ER004, and ER005 all cause DB003 downstream.
3. Clear that error, then wait one sync cycle.
4. If the connector is Active with a recent sync and the provider was slow (ER002 or ER004), no action is needed — the next cycle catches up.
5. If you need fresher data routinely, note that Starter syncs less often than Growth and Enterprise; an **Admin** can change plans in **Settings > Billing**.

If a connector reports a recent successful sync and DB003 stays for more than a day, contact support with the dashboard name and the source.
