# PL004 — Plan downgrade blocked by active connections

Polaris shows PL004 when you try to move to a smaller plan while your workspace still uses connectors or connections that the smaller plan does not cover.

## What PL004 protects you from

Without PL004, a downgrade would silently break live dashboards and reports. Instead Polaris stops the change and lists what stands in the way, which is usually one of:

- A **Salesforce** connection while moving off Enterprise
- A **HubSpot** or **Mailchimp** connection while moving to Starter
- More connections in use than the target plan allows
- More users than the target plan's seats

## How to complete a downgrade after PL004

1. Read the list in the PL004 message — it names every blocking connection or seat.
2. In **Settings > Connectors**, remove the connections the target plan does not include. Data already synced stays; future syncs stop.
3. In **Settings > Users**, remove users until you are within the target plan's seats.
4. Return to **Settings > Billing** and select the plan again.

Downgrading also shortens your data retention window, so export anything you need first from the dashboard **Export** button. If the blocking list looks wrong or names something you already removed, contact support before retrying.
