"""Build the Polaris knowledge base.

Generates help-center articles with Gemini, grounded in docs/product-polaris.md,
and writes each to kb/<id>.md. This corpus is the ground truth the RAG retrieves
from, and the set of articles that resolve the RAG-deflectable tickets.

Run from the repo root:  uv run python -m src.build_kb
"""

import pathlib

from src.llm import generate

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCT_DOC = ROOT / "docs" / "product-polaris.md"
KB_DIR = ROOT / "kb"

# (id, topic/feature, kind, title) — ~1-2 per feature for breadth.
ARTICLES = [
    ("getting-started", "Onboarding", "how-to", "Getting started with Polaris"),
    ("connectors-connect-ga4", "Connectors", "how-to", "How to connect Google Analytics 4"),
    ("connectors-connect-hubspot", "Connectors", "how-to", "How to connect your HubSpot CRM"),
    ("connectors-reauthorize-expired", "Connectors", "troubleshooting", "Reconnecting an expired connector (and who can do it)"),
    ("connectors-sync-delays", "Connectors", "troubleshooting", "Why your data looks stale: sync schedules and delays"),
    ("dashboards-build", "Dashboards", "how-to", "Building your first dashboard"),
    ("dashboards-not-loading", "Dashboards", "troubleshooting", "Dashboard won't load: what to check"),
    ("northstar-define", "North-Star Metric", "how-to", "Defining your north-star metric"),
    ("alerts-create", "Alerts", "how-to", "Creating threshold alerts"),
    ("alerts-not-firing", "Alerts", "troubleshooting", "My alert isn't firing"),
    ("reports-schedule", "Reports", "how-to", "Scheduling and exporting reports"),
    ("reports-not-arriving", "Reports", "troubleshooting", "A scheduled report didn't arrive"),
    ("attribution-setup-utms", "Attribution", "how-to", "Setting up UTMs and GA4 for accurate attribution"),
    ("attribution-models", "Attribution", "how-to", "Attribution models in Polaris, explained"),
    ("users-invite-roles", "Users & Workspace", "how-to", "Inviting teammates and understanding roles"),
    ("users-permission-denied", "Users & Workspace", "troubleshooting", "Permission denied: how roles gate actions"),
    ("billing-plans", "Billing", "how-to", "Plans and what each one includes"),
    ("billing-change-plan", "Billing", "how-to", "Upgrading or downgrading your plan"),
    ("security-privacy", "Security", "info", "How Polaris protects your data"),
]

PROMPT = """You are a technical writer producing a help-center article for Polaris.

PRODUCT CONTEXT (use for accuracy; do not paste it back verbatim):
{context}

Write ONE help-center article:
- Title: {title}
- Topic: {topic}
- Kind: {kind}

Requirements:
- Clear, concise SaaS help-center tone, in English. 150-300 words.
- Markdown. Start with a single H1 that matches the title exactly.
- how-to  -> numbered steps.
- troubleshooting -> likely causes + fixes, most common first.
- info -> short, plain explanation.
- Be specific to Polaris (connectors to Google Ads / GA4 / HubSpot / email;
  multi-tenant workspaces; roles Admin / Analyst / Viewer; scheduled syncs).
- End with a short "Still stuck? Contact support." line.
- Do NOT invent pricing numbers. Do NOT mention you are an AI.
"""


def main() -> None:
    KB_DIR.mkdir(exist_ok=True)
    context = PRODUCT_DOC.read_text(encoding="utf-8")
    for i, (aid, topic, kind, title) in enumerate(ARTICLES, 1):
        out = KB_DIR / f"{aid}.md"
        if out.exists():  # resumable: don't regenerate (saves quota)
            print(f"[{i}/{len(ARTICLES)}] {aid} — exists, skip", flush=True)
            continue
        print(f"[{i}/{len(ARTICLES)}] {aid} ...", flush=True)
        article = generate(PROMPT.format(context=context, title=title, topic=topic, kind=kind))
        out.write_text(article.strip() + "\n", encoding="utf-8")
    print(f"\nDone -> {len(ARTICLES)} articles in {KB_DIR}")


if __name__ == "__main__":
    main()
