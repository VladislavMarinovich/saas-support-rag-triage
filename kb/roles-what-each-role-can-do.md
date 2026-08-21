# Which role do I need? Admin, Analyst, and Viewer compared

Polaris has three roles, and most permission errors come down to holding the wrong one. This article compares them side by side and maps each role to the errors it produces, so you can tell which role you need before asking for a change. Roles are per workspace — the same person can be an Admin in one and a Viewer in another.

## Comparing the three roles at a glance

| What you want to do | Viewer | Analyst | Admin |
|---|---|---|---|
| Open dashboards and reports shared with you | yes | yes | yes |
| Receive alerts and scheduled reports | yes | yes | yes |
| Build or edit dashboards and widgets | no | yes | yes |
| Create, edit, or pause alerts | no | yes | yes |
| Create or edit scheduled reports, recipients, frequency | no | yes | yes |
| Export data on demand | no | yes | yes |
| Add, remove, or reconnect a connector | no | no | yes |
| Invite users or change someone's role | no | no | yes |
| Change the plan or the payment method | no | no | yes |

The pattern: **Viewer** reads, **Analyst** builds, **Admin** also holds credentials and billing.

## Which error each role produces, and what it tells you

Permission errors are a reliable way to identify your own role:

- **PF002 (role cannot edit)** — you are a Viewer trying to change a dashboard, alert, or report. You need Analyst.
- **PF006 (viewer cannot create alerts)** — same cause, specific to alerts. You need Analyst.
- **PF005 (only admins can reconnect)** — you are an Analyst trying to fix a connector. You need an Admin to run the reconnect; Analysts cannot promote themselves.
- **PF001 (no access to this dashboard)** — not about role level at all: the dashboard was never shared with you, or belongs to another workspace.

So PF002 and PF006 mean *ask to become an Analyst*, while PF005 means *ask an Admin to do this one thing for you*.

## Which role to request, and how to get it changed

1. **You only need to read dashboards and be notified** — Viewer is enough. An Analyst can add your address to any alert or report without changing your role.
2. **You need to build dashboards, alerts, or reports** — request Analyst.
3. **You need to connect data sources, manage users, or handle billing** — request Admin.

Ask an Admin to make the change in **Settings > Users**; your own row shows your current role. Changes apply immediately without signing out.

Keep at least two Admins in a workspace. With a single Admin who is unavailable, nobody can reconnect an expired connector, so dashboards quietly go stale behind ER001. If your role already shows what you need and the same error keeps appearing, sign out and back in, then contact support with the action you attempted.
