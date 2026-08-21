# AL004 — Alert paused after repeated failures

Polaris shows AL004 when an alert has failed to deliver enough times in a row that Polaris paused it instead of continuing to retry.

## Why an alert pauses itself

AL004 always follows another problem — usually repeated AL002 delivery failures, or an alert whose metric disappeared (AL003). Pausing avoids a loop of failing notifications, which is what damages sending reputation and floods logs.

The alert definition and its history stay intact. Only evaluation and notification stop.

## How to fix the cause and resume an alert after AL004

1. Open **Alerts** and select the paused alert; the failure history names the original error.
2. Fix that first: repair the Slack channel or recipient address for AL002, or re-point the metric for AL003.
3. Toggle the alert back **on**.
4. Lower the threshold temporarily to force one evaluation, and confirm the notification arrives.
5. Restore the real threshold.

Resuming an alert requires **Analyst** or **Admin**. If the alert delivers successfully on a manual test and pauses itself again, contact support with the alert name.
