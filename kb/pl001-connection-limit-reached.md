# PL001 — Connection limit reached

Polaris shows PL001 when you add a data source but your workspace already uses every connection your plan allows. The connector itself is available to you — you have simply run out of slots.

## How PL001 differs from a connector your plan excludes

PL001 counts **connections**, not connector types. Two Google Ads accounts are two connections even though they use one connector.

That distinction matters:

- **PL001** — the connector is included in your plan, but no slot is free
- **PF003** — the connector is not part of your plan at all
- **PL002** — an action in progress needs a higher plan to finish

Starter includes the fewest connections, Growth more, and Enterprise the most. Your exact allowance appears in **Settings > Billing**.

## How to free a connection or raise the limit after PL001

1. Open **Settings > Connectors** and list what is connected today, including sources nobody reports on any more.
2. Remove an unused connection — the slot frees immediately and you can add the new source.
3. If every connection is in use, ask an **Admin** to move the workspace up a plan in **Settings > Billing**. Plan changes take effect immediately and pro-rate mid-cycle.
4. Add the connector again.

Removing a connection deletes its future syncs but keeps the data already pulled. If **Settings > Billing** shows free connections and PL001 still blocks you, contact support with your workspace name.
