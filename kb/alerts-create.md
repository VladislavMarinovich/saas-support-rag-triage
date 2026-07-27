# Creating threshold alerts

Threshold alerts notify you when a metric crosses a boundary you define—helping you catch performance shifts in real time.

## How to create a threshold alert

1. **Navigate to Alerts**  
   From the left sidebar, select **Alerts**, then click **+ New Alert**.

2. **Choose your metric**  
   Select the metric you want to monitor (e.g., daily revenue, ad spend, lead count). This can come from any connected source: Google Ads, GA4, HubSpot, Salesforce, or your email platform.

3. **Set the threshold**  
   Define the condition:
   - Choose **above** or **below**
   - Enter the number that triggers the alert

4. **Select alert frequency**  
   Decide when Polaris checks your metric:
   - **Hourly** — most frequent checks
   - **Daily** — typical for business metrics
   - **Weekly** — for trending metrics

5. **Add recipients**  
   Enter email addresses for who should receive notifications. Only **Admin** and **Analyst** roles can create or edit alerts; **Viewer** can see alert history.

6. **Save and activate**  
   Click **Create Alert**. The alert is live immediately and will fire the first time your metric crosses the threshold.

## Tips

- Ensure your data source is connected and syncing regularly (check **Connectors** if you see stale data).
- Test your alert by temporarily adjusting the threshold to a value your metric should cross soon.
- Alerts respect your workspace's data refresh schedule—thresholds are checked only when new data arrives.

Still stuck? [Contact support.](#)
