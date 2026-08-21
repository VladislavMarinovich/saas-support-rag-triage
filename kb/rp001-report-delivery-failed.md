# RP001 — Report delivery failed

Polaris shows RP001 when a scheduled report was generated but could not be delivered to one or more of its destinations.

## What RP001 means about your report

RP001 separates two things people usually merge: the report ran, and the delivery failed. The file exists — you can still download it from **Reports** — but the email or Slack message never landed.

Common reasons behind RP001:

- A recipient address that bounced (mailbox full, address no longer exists)
- A Slack channel Polaris was removed from, or that was archived
- A recipient domain rejecting mail from `reports@polaris.io`
- A file too large for the destination to accept (see RP004)

RP001 is about delivery only. If the report never ran at all, look at RP003 (generation timed out) instead.

## How to fix RP001 and resend the report

1. Open **Reports** and select the report flagged with RP001 — the delivery log names which destination failed.
2. Fix that destination: correct the recipient address, or re-invite the Polaris app to the Slack channel.
3. Ask recipients to allow `reports@polaris.io` if a whole domain is rejecting messages.
4. Use **Send now** to retry immediately, rather than waiting for the next scheduled run.
5. Confirm the delivery log shows success.

Creating or editing a report schedule requires **Analyst** or **Admin**. If the log shows success but nobody received the report, ask recipients to check spam and promotions folders first, then contact support with the report ID.
