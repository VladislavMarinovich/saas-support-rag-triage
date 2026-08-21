# RP003 — Report generation timed out

Polaris shows RP003 when building the report file takes longer than the allowed window, so nothing is produced and nothing is sent.

## What makes a report time out

RP003 is about size and complexity, not delivery. The usual causes:

- A very long date range, especially with daily breakdowns
- Many widgets in one report, each querying a different source
- A source that was syncing slowly while the report ran (see ER004)
- Several large reports scheduled at the same minute

Because nothing was generated, there is no partial file to download — unlike RP001, where the file exists but delivery failed.

## How to get a large report to complete

1. Shorten the date range, then re-run with **Send now** to confirm it completes.
2. Split one heavy report into two smaller ones by source or by section.
3. Move the schedule off the top of the hour so it does not compete with other reports and syncs.
4. Check **Settings > Connectors** for slow or failing syncs before the report window, and let those finish first.

If a small report on a short range still returns RP003, contact support with the report ID and its scheduled time.
