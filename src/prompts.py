"""
Prompt builder: turns a TicketSpec into an instruction for the LLM to write the
customer's inbound message (subject + body).

The golden rule: the text must read like a real customer wrote it and must NOT
reveal the ground-truth labels (priority/type/routing names). Those stay as the
answer key; leaking them into the text would make the triage task trivial and
fake. See docs/dataset-spec.md §2.
"""

from __future__ import annotations

from src.sampler import TicketSpec

# One-line product grounding so the model uses the right vocabulary.
_POLARIS = (
    "Polaris is a multichannel analytics SaaS (Google Ads, GA4, CRM, email) with "
    "connectors, dashboards, alerts, attribution, scheduled reports, a north-star "
    "metric tracker, team roles (Admin/Analyst/Viewer), and billing plans."
)

# Emotion -> tone guidance (never name the emotion in the text).
_TONE = {
    "neutral": "calm and matter-of-fact",
    "confused": "unsure, not clear on what is happening or what to do",
    "overwhelmed": "a little lost, like there is too much to handle",
    "frustrated": "annoyed that something isn't working",
    "angry": "upset and blunt, maybe demanding — but never abusive or profane",
    "anxious": "worried, especially about their data or account safety",
}

# Length band -> concrete size guidance (calibrated on the EDA).
_LENGTH = {
    "short": "one short sentence, under ~120 characters",
    "medium": "2–4 sentences, roughly 120–500 characters",
    "long": "a longer, detailed message with specifics, 500+ characters",
}

# Channel -> style guidance.
_CHANNEL = {
    "chat": "a live-chat message: terse, lowercase is fine, often no greeting; leave the subject empty",
    "email": "an email: include a short subject line and a slightly more complete message",
    "in_app": "an in-app help message: short and direct; subject optional",
}


def build_prompt(spec: TicketSpec) -> str:
    """Compose the generation prompt for one ticket spec."""
    formality = (
        "This user is an Admin on the Enterprise plan — a bit more professional."
        if spec.user_role == "admin" and spec.plan == "enterprise"
        else "This user is a Viewer — more of a layperson, less technical."
        if spec.user_role == "viewer"
        else "Write in a normal, everyday customer voice."
    )
    urgency = (
        "Convey that this is blocking their work / urgent."
        if spec.priority in ("high", "critical")
        else ""
    )
    # Ground the plan so the model references the real tier instead of inventing
    # names like "standard" or "mid-tier" (seen in validation).
    plan_line = (
        f"Your Polaris plan is {spec.plan.capitalize()} (the only tiers are "
        f"Starter, Growth, Enterprise). If you mention your plan, use that exact "
        f"name — never invent a tier."
    )

    return f"""You are simulating a CUSTOMER writing an inbound support ticket to Polaris.

{_POLARIS}

The situation: {spec.seed_text}.

Write it as {_CHANNEL[spec.channel]}.
Tone: sound {_TONE[spec.sentiment]}.
Length: {_LENGTH[spec.length_band]}.
{formality}
{plan_line}
{urgency}

Realism rules:
- Write in the first person, as the customer. Do NOT sound like documentation.
- It's fine (and good) to be imprecise, use lowercase, small typos, or partial
  info — real people don't write clean bug reports.
- Do NOT mention priority, routing, ticket type, or that this is synthetic.
- No real names, emails, phone numbers, or company names — use placeholders
  like "my workspace" or "our GA4 account".

Return ONLY a JSON object, nothing else:
{{"subject": "<short subject or empty string>", "body": "<the message>"}}"""
