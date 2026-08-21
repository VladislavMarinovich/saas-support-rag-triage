# RP006 — Report schedule paused automatically

Polaris shows RP006 when a scheduled report has failed enough consecutive times that the schedule was paused to stop it retrying indefinitely.

## Why a schedule pauses itself

RP006 is a consequence, never a cause: something else was failing first — repeated delivery failures (RP001), invalid destinations (RP002), timeouts (RP003), or a bounced recipient (RP005). Pausing prevents dozens of failed sends and the spam complaints that follow.

The report definition, its widgets, and its history are untouched. Only the automatic sending is off.

## How to fix the underlying problem and resume the schedule

1. Open **Reports** and select the paused report. The failure history names the original error code.
2. Fix that error first — correct the destination, shorten the range, or replace the bounced address.
3. Use **Send now** and confirm one successful delivery.
4. Toggle the **schedule** back on.
5. Check the next run time is what you expect.

Resuming a schedule requires **Analyst** or **Admin**. If the report sends successfully with **Send now** but pauses itself again on the next scheduled run, contact support with the report ID.
