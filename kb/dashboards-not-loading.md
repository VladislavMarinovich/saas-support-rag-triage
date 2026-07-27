# Dashboard won't load: what to check

If a dashboard isn't loading or appears blank, work through these common causes:

## 1. Check your internet connection
Reload the page. If other Polaris features work, proceed to step 2.

## 2. Verify connector status
Dashboards depend on active data connectors (Google Ads, GA4, HubSpot, Mailchimp, etc.). A broken connector blocks data flow.

- Go to **Workspace Settings** → **Connectors**.
- Look for any connectors showing a warning icon or "Auth expired."
- If found, an Admin user must re-authenticate the connector. Viewer and Analyst roles cannot reconnect.

## 3. Wait for the scheduled sync
Data syncs on a set schedule (hourly or daily, depending on your plan). If you just connected a source or expect fresh data, the dashboard may still be waiting for the next sync window. Check the timestamp on the dashboard for the last data refresh.

## 4. Check your permissions
If you're an Analyst or Viewer, confirm an Admin hasn't restricted your access to this dashboard. Request the Admin to verify your role in **Workspace Settings** → **Users**.

## 5. Try a hard refresh
Press **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac) to clear your browser cache and reload.

---

**Still stuck?** If the dashboard is still blank after these steps, or if you see an error message, [contact support](mailto:support@polaris.example.com) with the dashboard name and any error details.
