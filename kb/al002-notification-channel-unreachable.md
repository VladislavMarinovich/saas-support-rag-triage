# AL002 — Notification channel unreachable

Polaris shows AL002 when an alert fired correctly but the notification could not be delivered to its channel.

## What AL002 means about the alert versus the channel

The alert worked: the condition was met and the event is in the alert history. What failed is the hop to email or Slack. That is why you can see an alert listed as fired and still have received nothing.

Common causes:

- The Polaris app was removed from the Slack channel, or the channel was archived
- A recipient address bounced or no longer exists
- A private Slack channel Polaris was never invited to
- A recipient's mail gateway rejecting `alerts@polaris.io`

## How to restore delivery after AL002

1. Open **Alerts**, select the alert, and check its recipients and channel.
2. For Slack, re-invite the Polaris app to the channel, or pick a different channel from the list.
3. For email, correct or replace the failing address.
4. Ask recipients to allow mail from `alerts@polaris.io` if a whole domain is rejecting it.
5. Trigger a test by lowering the threshold temporarily and confirm the notification arrives.

If the channel is reachable for other alerts and AL002 keeps appearing on one, contact support with the alert name and the channel.
