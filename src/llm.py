"""LLM client for Polaris synthetic-data generation (Google Gemini via AI Studio).

Reused by the knowledge-base builder and the ticket generator. The API key is
read from the gitignored `.env` file — never hard-code it here.
"""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

# Fast, cheap, current-gen model — good for generating KB articles and tickets.
# Pinned (not a *-latest alias) so the generation is reproducible.
# If this model id errors, run `list_models()` below to see what's available.
DEFAULT_MODEL = "gemini-3.5-flash"

_api_key = os.environ.get("GOOGLE_API_KEY")
if not _api_key or _api_key == "PASTE_YOUR_KEY_HERE":
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Copy .env.example to .env and paste your key "
        "(get one at https://aistudio.google.com)."
    )

client = genai.Client(api_key=_api_key)


def generate(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to Gemini and return the plain-text response."""
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text


def list_models() -> None:
    """Print available model ids (use if DEFAULT_MODEL errors)."""
    for m in client.models.list():
        print(m.name)


if __name__ == "__main__":
    # Smoke test — run:  uv run python src/llm.py
    print(generate("Reply in one short sentence confirming the connection works."))
