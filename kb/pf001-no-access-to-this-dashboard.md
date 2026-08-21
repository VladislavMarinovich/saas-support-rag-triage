# PF001 — You don't have access to this dashboard

Polaris shows PF001 when you open a dashboard your role or your workspace membership does not cover. The dashboard exists; it is simply not shared with you.

## What PF001 means about your role

PF001 is a permission decision, not a bug or an outage. It appears when:

- The dashboard was created in a workspace you do not belong to
- An Admin restricted the dashboard to a narrower group
- Your role was changed to **Viewer** and the dashboard requires **Analyst** access to open

Note that PF001 is different from a dashboard that loads but shows nothing: an empty dashboard is a data problem (see DB002), while PF001 blocks the page entirely.

## How to get access after PF001

1. Copy the dashboard name or link from the PF001 message.
2. Ask an **Admin** in your workspace to share it with you, or to confirm your role in **Settings > Users**.
3. If you should be an **Analyst** but appear as **Viewer**, ask the Admin to change your role — role changes apply immediately.
4. Reload the page after the change.

If you are already an Admin and still see PF001, you are probably signed in to a different workspace than the one that owns the dashboard. Check the workspace name in the top bar, then contact support with the dashboard link if it still fails.
