# DB005 — Dashboard exceeds widget limit

Polaris shows DB005 when you add a widget to a dashboard that already holds as many as one dashboard can render reliably — this is why **Add Card** stops working on a crowded dashboard.

## Why dashboards have a widget ceiling

Widgets are the cards on a dashboard, and each card is its own query against a source. Past a certain count, a dashboard becomes slow enough to hit load failures (DB001) and to time out the reports built on it (RP003). DB005 stops that before it happens.

The new widget is not saved while DB005 is open; the existing layout is untouched.

## How to work around DB005

1. Remove widgets nobody uses — old campaign breakdowns are the usual dead weight.
2. Split the dashboard by theme: one for paid media, one for CRM and revenue, one for web analytics. Cross-linked dashboards load faster than one crowded page.
3. Replace several near-identical widgets with one that uses a breakdown dimension.
4. Add the new widget to the smaller dashboard.

Splitting a dashboard needs **Analyst** or **Admin**. If a dashboard with few widgets returns DB005, contact support with the dashboard name.
