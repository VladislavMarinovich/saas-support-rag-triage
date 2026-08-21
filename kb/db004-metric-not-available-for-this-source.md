# DB004 — Metric not available for this source

Polaris shows DB004 when a widget asks for a metric that the selected source does not provide.

## Why metrics differ between sources

Every provider exposes its own fields, and they do not overlap neatly. Google Ads reports ad spend; Google Analytics does not. Google Analytics reports sessions; HubSpot does not. Salesforce reports opportunity amounts; Meta Ads does not.

DB004 appears when a widget was pointed at a source that lacks the requested field — often after duplicating a widget and switching its source, or after a report template was reused across workspaces.

## How to fix a widget after DB004

1. Open the dashboard and edit the widget flagged DB004.
2. Either pick a metric the current source provides, or switch the source to one that has the metric you want.
3. For blended reporting, use two widgets side by side — one per source — instead of forcing one widget to span both.
4. Save and confirm the widget resolves.

Editing widgets requires **Analyst** or **Admin**. If the metric is documented for that source and DB004 persists, contact support with the dashboard name, the widget, and the source.
