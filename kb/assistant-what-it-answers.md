# What the Polaris assistant can answer

Polaris includes an LLM support assistant that answers questions about the product from the knowledge base. It is available on every plan, and it is deliberately narrow about what it will answer.

## Questions the assistant answers well

The assistant is built for documentation questions — how the product works and how to fix a specific error:

- **How-to questions** — "how do I schedule a weekly report", "how do I connect Meta Ads"
- **Error codes** — "what does ER005 mean", "how do I fix PF003"
- **Concepts** — "how does multi-touch attribution work", "what can a Viewer do"
- **Plan and connector coverage** — "which plan includes Salesforce"

Ask one thing at a time and use product words — the connector name, the module, or the error code. A single specific question retrieves a better answer than three combined.

## Questions the assistant will not answer, and why

- **Your own numbers** — it cannot read your workspace, so it cannot tell you last week's spend or whether your sync ran. It returns AG003 and points you to the dashboard. This keeps your metrics away from the language model.
- **Topics with no article** — it returns AG002 rather than assembling a plausible-sounding answer from unrelated pages. An honest "I don't know" is more useful than a confident guess you cannot verify.
- **Requests only staff can act on** — billing disputes, account deletion, security incidents. It returns AG004 and routes you to a person.

The assistant replies in the language you asked in, including its refusals. If it is unreachable altogether you will see AG001, which is temporary — the knowledge base is still readable directly.
