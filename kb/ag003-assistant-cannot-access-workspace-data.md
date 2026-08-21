# AG003 — Assistant cannot access your workspace data

Polaris returns AG003 when you ask the assistant something that would require reading your own numbers — your spend, your deals, your dashboards — which it is not able to do.

## What the assistant can and cannot see

The assistant reads Polaris documentation, not your workspace. It can explain how attribution works, why ER005 appears, or how to schedule a report. It cannot tell you last week's spend, which campaign performed best, or whether your sync ran.

This is a privacy boundary, not a bug: keeping the assistant away from workspace data means your metrics are never sent to a language model.

## How to get the answer you wanted after AG003

1. For your own numbers, open the relevant dashboard, or export the data from the dashboard **Export** button.
2. For sync state, check **Settings > Connectors** — it shows the last successful sync per source.
3. For monitoring rather than checking, create an alert so Polaris notifies you when a metric crosses a threshold.
4. Ask the assistant the how-to version of your question ("how do I build a spend-by-campaign widget") instead of the data version.

If you believe the answer is documented and not account-specific, rephrase with product terms and ask again; contact support if it still returns AG003.
