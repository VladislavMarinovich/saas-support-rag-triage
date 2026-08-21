# PF002 — Role cannot edit

Polaris shows PF002 when you try to change something your role can only read: editing a dashboard widget, changing an alert threshold, or updating a report schedule as a **Viewer**.

## What PF002 means and which actions it blocks

PF002 is raised at the moment you save, not when you open the item — so you may be able to see an edit screen and still be blocked on save.

Typical actions that trigger PF002 for a Viewer:

- Adding, resizing, or deleting dashboard widgets
- Creating or editing alerts
- Changing a report's frequency or recipients
- Renaming or deleting a dashboard

Admins and Analysts do not get PF002 for these actions. Reconnecting a connector is different: that is Admin-only and raises PF005 for Analysts.

## How to resolve PF002

1. Check your role in **Settings > Users** — your own row shows it.
2. If you need to build or edit, ask an Admin to change your role from **Viewer** to **Analyst**.
3. If the change is one-off, ask an Analyst or Admin to make it for you.
4. Retry the action after the role change; it takes effect immediately without signing out.

If your role already says Analyst or Admin and PF002 keeps appearing on save, contact support with the item name and the action you attempted.
