# DB001 — Dashboard failed to load

Polaris shows DB001 when a dashboard cannot finish loading: the page opens but the widgets never resolve, or an error replaces the layout.

## What DB001 points at

DB001 is about the dashboard failing to render, which narrows the causes considerably:

- One widget is querying a source that is failing right now (a connector showing ER001, ER005, or ER004)
- The dashboard holds many heavy widgets over a long date range and the queries exceed the load window
- A metric behind a widget was removed, so the widget cannot resolve

DB001 is not a permission problem — that is PF001, which blocks the page entirely — and it is not an empty widget on a dashboard that otherwise loads, which is DB002.

## How to get a dashboard loading again after DB001

1. Note the dashboard name, then open **Settings > Connectors** and check for error codes on the sources it uses. Clear those first.
2. Shorten the dashboard's date range and reload — if it loads, the size was the problem.
3. Remove or rebuild the widget that fails to resolve; add it back once the source is healthy.
4. Force a fresh load with **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac) to rule out a stale cached page.

Editing widgets requires **Analyst** or **Admin**. If every connector is Active, the range is short, and DB001 persists, contact support with the dashboard name.
