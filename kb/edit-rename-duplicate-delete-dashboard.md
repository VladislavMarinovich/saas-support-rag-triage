# Renaming, duplicating, and deleting a dashboard

Beyond editing widgets, you can manage the dashboard itself: give it a clearer name, copy it as a starting point, or remove it. All three need **Analyst** or **Admin**.

## Renaming a dashboard without breaking anything

1. Open the dashboard and use the dashboard menu (**⋯**) next to its title.
2. Choose **Rename** and enter the new name.
3. Save.

Renaming is safe: scheduled reports built on the dashboard keep working, and alerts are unaffected because they reference metrics, not dashboard names. Anyone who bookmarked the dashboard keeps their link.

## Duplicating a dashboard as a template

1. From the dashboard menu, choose **Duplicate**.
2. Name the copy something distinct — "Q3 Paid Performance", not "Copy of...".
3. Edit the copy's widgets for the new period, campaign, or source.

Duplicating is the fastest way to reuse a layout, but check each widget after switching sources: a duplicated widget pointed at a source that lacks its metric returns DB004.

## Deleting a dashboard, and what it takes with it

1. From the dashboard menu, choose **Delete** and confirm.
2. Scheduled reports built on that dashboard stop producing output — delete or re-point them too, or they will fail on their next run.
3. Alerts survive, since they watch metrics rather than dashboards.

Deleting a dashboard does not delete synced data: the connectors keep their history and you can rebuild an equivalent dashboard at any time. Deleting an entire **workspace or account** is a different matter and cannot be done from Settings — that request is reviewed by staff. If a dashboard reappears after deletion, contact support with its name.
