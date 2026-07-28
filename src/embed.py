"""Embed text via Gemini `text-embedding-005` on Vertex AI (768-dim).

One reusable primitive used by BOTH sides of the system:
  - indexing: embed the KB chunks → store in the vector DB
  - query:    embed an incoming ticket/question → search
  - (later) the same vectors double as features for the triage classifier.

Auth = Application Default Credentials (same as src/llm.py's Vertex path).
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-005")

_client = None


def _vertex():
    global _client
    if _client is None:
        from google import genai

        project = os.environ.get("GOOGLE_CLOUD_PROJECT", "polaris-triage-demo")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        _client = genai.Client(vertexai=True, project=project, location=location)
    return _client


def embed_texts(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Return one embedding vector per input text (batched)."""
    model = model or EMBED_MODEL
    vectors: list[list[float]] = []
    batch_size = 100  # Vertex caps how many inputs per request
    # send the texts in batches, collecting one vector per input
    for i in range(0, len(texts), batch_size):
        resp = _vertex().models.embed_content(model=model, contents=texts[i:i + batch_size])
        vectors.extend(e.values for e in resp.embeddings)
    return vectors


if __name__ == "__main__":
    v = embed_texts(["connection test"])
    print(f"model={EMBED_MODEL}  dim={len(v[0])}")
