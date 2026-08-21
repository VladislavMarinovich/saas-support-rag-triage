# RP002 — Invalid destination

Polaris shows RP002 when a report's destination cannot be used as written: the email address is malformed, or the Slack channel does not exist in your connected workspace.

## How RP002 differs from a delivery that fails

RP002 is caught before sending, so no attempt is made. That is the difference from RP001, where Polaris tried to deliver and the destination refused.

Typical RP002 causes:

- A typo in an address (missing `@`, a trailing comma, two addresses in one field)
- A Slack channel renamed after the report was set up
- A private Slack channel that Polaris was never invited to
- A distribution list that no longer resolves

## How to fix RP002

1. Open **Reports**, select the report, and look at the **recipients** field.
2. Enter one address per entry, comma-separated, and remove stray characters.
3. For Slack, pick the channel from the list rather than typing it, so the name matches exactly. Invite the Polaris app to private channels first.
4. Save, then use **Send now** to confirm the destination is accepted.

If the address and channel are both correct and RP002 persists, contact support with the report ID and the destination you configured.
