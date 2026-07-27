# Permission denied: how roles gate actions

In Polaris, not all users can perform all actions. Your role—**Admin**, **Analyst**, or **Viewer**—determines what you can do in your workspace.

## Common permission issues

### "I can't reconnect a connector"
**Cause:** Reconnecting connectors (Google Ads, GA4, HubSpot, Mailchimp, etc.) requires **Admin** permissions.

**Fix:** Ask an Admin in your workspace to reconnect the integration. If the connector's auth has expired, your data sync may pause until it's refreshed.

### "I can't see a dashboard or metric"
**Cause:** Your role may not have visibility to that dashboard, or your Admin hasn't shared it with you yet.

**Fix:** Contact your Admin to grant you access or confirm the dashboard is shared with your role level.

### "I can't invite team members"
**Cause:** Only **Admins** can manage workspace users and assign roles.

**Fix:** If you need to add users, ask your Admin. If you're the first Admin, you already have this permission.

### "I can't modify alerts or reports"
**Cause:** **Viewers** can only view dashboards; **Analysts** can create and edit. **Admins** have full access.

**Fix:** Check your assigned role. If you need edit permissions, ask your Admin to promote you to Analyst.

## Role reference

- **Admin** — manage users, reconnect connectors, all creation/edit/delete
- **Analyst** — create dashboards, alerts, reports; cannot manage users or connectors
- **Viewer** — read-only access to shared content

Still stuck? [Contact support.](#)
