# Changing a report's frequency and recipients

An existing scheduled report can be re-timed and re-addressed without rebuilding it. Editing a schedule requires **Analyst** or **Admin**.

## Changing how often a report is sent

1. Open **Reports** and click the report name.
2. In the schedule section, change the **frequency** — daily, weekly, or monthly.
3. Set the **day and time** you want it delivered. Avoid the top of the hour if you run several large reports, since simultaneous generation can cause RP003.
4. Save. The **next run time** updates immediately — check it matches what you expect.

Turning the schedule off with the toggle keeps the report and its history; it just stops sending. That is also how you resume a report that paused itself after repeated failures (RP006).

## Changing who receives a report

1. In the same settings, edit the **recipients** field.
2. Enter one address per entry, comma-separated. A malformed entry returns RP002 before anything is sent.
3. For Slack, pick the channel from the list rather than typing it, and make sure the Polaris app is invited to private channels.
4. Remove addresses that bounced — a repeatedly failing recipient causes RP005 and can pause the whole schedule.
5. Save, then use **Send now** to confirm the new recipients receive it.

Recipients do not need a Polaris account to receive a report, and adding someone to a report does not give them access to the dashboard behind it. If a saved recipient stops receiving reports while others get them, check spam folders first, then contact support with the report ID.
