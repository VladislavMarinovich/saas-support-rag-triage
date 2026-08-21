# PL003 — Payment failed

Polaris shows PL003 when a scheduled charge for your plan is declined. Your workspace keeps running for a grace period while the payment is retried.

## What PL003 affects and what keeps working

During the grace period, dashboards, connectors, alerts, and scheduled reports all continue as normal — PL003 is a billing state, not a service cut. What it does block is anything that changes your plan: adding connections beyond your current allowance, or moving up a plan, until the balance clears.

Only **Admins** see the PL003 banner, since only they can act on billing.

## How to clear PL003

1. Open **Settings > Billing** as an **Admin**.
2. Review the payment method on file — the most common causes are an expired card, a new expiry date, or a billing address that no longer matches the card.
3. Update the payment method, then choose **Retry payment**.
4. Confirm the plan status returns to active.

Payment disputes, refunds, and chargebacks are not handled in the product: a member of our billing staff has to review those cases directly. If the charge looks wrong rather than simply declined, contact support and ask for a billing review instead of retrying the payment.
