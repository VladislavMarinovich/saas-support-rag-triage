# PF006 — Viewer cannot create alerts

Polaris shows PF006 when someone with the **Viewer** role tries to create or edit a threshold alert.

## What PF006 means about alerts and roles

Viewers can see alert history and receive notifications if their address is on the recipient list, but they cannot define the conditions. Creating and editing alerts requires **Analyst** or **Admin**.

This is why a Viewer can be notified about an alert they are not allowed to change — receiving an alert and owning it are separate things in Polaris.

## How to get an alert created after PF006

1. If you only need to be notified, ask an Analyst or Admin to add your email to the alert's recipients — no role change needed.
2. If you need to create or tune alerts yourself, ask an Admin to change your role to **Analyst** in **Settings > Users**.
3. Retry immediately after the change; roles apply without signing out.

If your role already shows Analyst and PF006 keeps appearing, contact support with the metric you were setting the alert on.
