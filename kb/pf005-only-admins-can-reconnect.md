# PF005 — Only admins can reconnect a connector

Polaris shows PF005 when an Analyst or Viewer tries to reconnect a data source. Reconnecting requires OAuth permissions that only the **Admin** role holds.

## Why PF005 exists even when the fix looks obvious

You may be able to see that a connector needs attention — ER001 or ER005 on the card — and still be blocked from fixing it. That is deliberate: reconnecting hands Polaris credentials for your Google Ads, Meta Ads, Google Analytics, HubSpot, Salesforce, or Mailchimp account, so it is restricted to Admins.

PF005 blocks only the reconnect action. Analysts keep full access to dashboards, alerts, and reports built on that source.

## What to do when you hit PF005

1. Note which connector needs reconnecting and the error code on its card.
2. Open **Settings > Users** to see who holds the **Admin** role in your workspace.
3. Ask that person to run the reconnect — it takes under a minute from **Settings > Connectors**.
4. If your only Admin is unavailable, another Admin must be appointed first; Analysts cannot promote themselves.

If you are listed as an Admin and still get PF005, sign out and back in so the new role loads, then contact support if it persists.
