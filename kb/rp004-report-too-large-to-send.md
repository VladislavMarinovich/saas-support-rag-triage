# RP004 — Report too large to send

Polaris shows RP004 when a report is generated successfully but the file exceeds what the destination accepts — most often an email attachment size limit.

## What RP004 means and where the file still lives

The report is complete and stored: you can download it from **Reports** at any time. Only the attachment was refused, which is why the schedule shows a failure while the file itself is fine.

Email destinations hit RP004 far more often than Slack. Long date ranges exported as PDF, and CSV exports of very wide tables, are the usual culprits.

## How to deliver a large report after RP004

1. Open **Reports** and download the file directly to confirm it is intact.
2. Change the export format — CSV is much smaller than PDF for the same data.
3. Shorten the date range, or split the report into monthly instalments.
4. Send to a Slack channel instead of email, which tolerates larger files.
5. Re-run with **Send now** and check the delivery log.

If a small file is still refused with RP004, the recipient's mail server may impose a stricter limit than expected; contact support with the report ID and the destination.
