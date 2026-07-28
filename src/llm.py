"""LLM client for Polaris synthetic-data generation.

Two interchangeable providers behind ONE stable `generate()` interface, so the
KB builder and ticket generator never change when we swap models:

  - anthropic (default): Claude via the Anthropic API ($5 free credit).
  - vertex: Gemini via Vertex AI (uses GCP credits, no daily cap; for the bulk).

Select with the LLM_PROVIDER env var, e.g.:
  LLM_PROVIDER=vertex uv run python -m src.generate_tickets --n 25 ...

Anthropic auth = ANTHROPIC_API_KEY in the gitignored .env.
Vertex auth = Application Default Credentials (gcloud auth application-default
login) + GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION. No keys in code, ever.
"""

import os

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

# Default model per provider (both cheap/fast; good for volume generation).
ANTHROPIC_MODEL = "claude-haiku-4-5"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
DEFAULT_MODEL = ANTHROPIC_MODEL  # kept for backward-compat with existing imports

# Clients are created lazily so importing this module needs only the ONE
# provider's credentials you actually use (not both).
_anthropic_client = None
_vertex_client = None


def _anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key or key == "PASTE_YOUR_KEY_HERE":
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file "
                "(create a key at https://console.anthropic.com)."
            )
        # SDK auto-retries 429/5xx with backoff; bump from the default 2.
        _anthropic_client = anthropic.Anthropic(api_key=key, max_retries=5)
    return _anthropic_client


def _vertex():
    global _vertex_client
    if _vertex_client is None:
        from google import genai

        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "polaris-triage-demo")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        # vertexai=True routes through Vertex (ADC auth), not AI Studio (API key).
        _vertex_client = genai.Client(vertexai=True, project=project, location=location)
    return _vertex_client


def generate(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 4096,
    provider: str | None = None,
) -> str:
    """Send a prompt to the selected provider and return the plain-text reply.

    `provider` overrides the LLM_PROVIDER env var for a single call (handy for
    A/B comparisons); `model` overrides that provider's default model.
    """
    provider = (provider or PROVIDER).lower()

    if provider == "anthropic":
        response = _anthropic().messages.create(
            model=model or ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in response.content if b.type == "text")

    if provider in ("vertex", "gemini"):
        from google.genai import types

        response = _vertex().models.generate_content(
            model=model or GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return response.text or ""

    raise ValueError(f"unknown LLM_PROVIDER: {provider!r} (use 'anthropic' or 'vertex')")


if __name__ == "__main__":
    # Smoke test — run:  uv run python src/llm.py
    # or against Vertex:  LLM_PROVIDER=vertex uv run python src/llm.py
    print(f"provider={PROVIDER}")
    print(generate("Reply in one short sentence confirming the connection works."))
