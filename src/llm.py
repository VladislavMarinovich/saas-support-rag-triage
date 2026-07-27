"""LLM client for Polaris synthetic-data generation (Anthropic Claude).

Reused by the knowledge-base builder and the ticket generator. The API key is
read from the gitignored `.env` file — never hard-code it here.
"""

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Cheap, fast model — good for generating KB articles and tickets at volume.
# Swap to "claude-sonnet-5" if you want higher-quality prose (higher cost).
DEFAULT_MODEL = "claude-haiku-4-5"

_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not _api_key or _api_key == "PASTE_YOUR_KEY_HERE":
    raise RuntimeError(
        "ANTHROPIC_API_KEY is not set. Add it to your .env file "
        "(create a key at https://console.anthropic.com)."
    )

# The SDK auto-retries 429 / 5xx with exponential backoff; bump the default (2)
# for robustness during bulk generation.
client = anthropic.Anthropic(api_key=_api_key, max_retries=5)


def generate(prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 4096) -> str:
    """Send a prompt to Claude and return the plain-text response."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


if __name__ == "__main__":
    # Smoke test — run:  uv run python src/llm.py
    print(generate("Reply in one short sentence confirming the connection works."))
