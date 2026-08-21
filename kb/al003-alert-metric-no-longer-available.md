# AL003 — Alert metric no longer available

Polaris shows AL003 when an alert points at a metric that no longer exists in your workspace, so there is nothing left to evaluate.

## What removes a metric from under an alert

AL003 is usually the aftermath of a change somewhere else:

- The connector feeding the metric was removed, or its connection slot was freed to make room for another (see PL001)
- A plan change dropped the connector — HubSpot or Mailchimp after moving to Starter, Salesforce after moving off Enterprise
- The source property or ad account was deleted and recreated, so the old metric ID is gone
- A custom metric on a dashboard was deleted while an alert still referenced it

The alert is not deleted; it is left pointing at nothing, which is why it neither fires nor errors on schedule.

## How to repair an alert after AL003

1. Open **Alerts** and select the one flagged AL003 — it names the metric it expected.
2. Check **Settings > Connectors** for the source. If it was removed, reconnect it, or pick a metric from a source you still have.
3. Re-select the metric on the alert and set the threshold again, since scales differ between sources.
4. Save and confirm the alert evaluates on the next sync.

If the metric is present on your dashboards and the alert still reports AL003, contact support with the alert name and the metric.
