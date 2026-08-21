# AL001 — Alert did not fire

Polaris shows AL001 when an alert you expected to trigger did not, and the cause is on the alert side rather than the data side.

## What AL001 means about your threshold and schedule

An alert only evaluates when new data arrives, on your workspace's sync schedule. AL001 means an evaluation happened and the condition was not met, or no evaluation happened at all because the alert was paused or its metric never updated.

The three things behind almost every AL001:

- The threshold is set beyond what the metric actually reaches — "above 50" when the metric peaks at 30
- The alert is toggled off
- The alert checks hourly but the source syncs daily, so most checks see identical data

AL001 is not about delivery. If the alert fired but nobody got the message, that is AL002.

## How to diagnose AL001

1. Open **Alerts** and select the alert. Compare its condition with the metric's current value on your dashboard.
2. Adjust the threshold to a value the metric plausibly crosses, and save.
3. Confirm the alert is toggled **on** and check its frequency against how often the source syncs.
4. Verify the source is not stuck — a connector showing ER001 or ER005 feeds no new data, so nothing can cross the threshold.
5. Test by moving the threshold temporarily to a value the metric already exceeds; the alert should fire on the next check.

Creating and editing alerts requires **Analyst** or **Admin**. If the metric clearly crosses a threshold on an active alert and AL001 persists, contact support with the alert name.
