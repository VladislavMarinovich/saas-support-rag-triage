"""Pinecone vector store for the Polaris KB (RAG retrieval).

Indexing:  chunk the KB -> embed -> upsert vectors (+ metadata) into Pinecone.
Query:     embed the question -> Pinecone returns the nearest chunks.

For now the chunk text lives in Pinecone metadata (simplest end-to-end retrieval,
no second store needed). Later, Mongo becomes the text system-of-record and
Pinecone keeps just id + vector + light metadata.

Auth: PINECONE_API_KEY in the gitignored .env.
Run:  python -m src.vectorstore   (indexes the KB, then runs a sample query)
"""

from __future__ import annotations

import os
import time

from dotenv import load_dotenv

from src.chunk_kb import chunk_kb
from src.embed import embed_texts

load_dotenv()

INDEX_NAME = os.environ.get("PINECONE_INDEX", "polaris-kb")
DIM = 768  # text-embedding-005 output dimension


def _client():
    from pinecone import Pinecone

    key = os.environ.get("PINECONE_API_KEY")
    if not key:
        raise RuntimeError("PINECONE_API_KEY is not set. Add it to your .env "
                           "(create one at https://app.pinecone.io).")
    return Pinecone(api_key=key)


def get_index(create: bool = True):
    """Return the Pinecone index handle, creating a serverless index if missing."""
    from pinecone import ServerlessSpec

    pc = _client()
    if create and not pc.has_index(INDEX_NAME):
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIM,
            metric="cosine",  # matches how we compared vectors by hand
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),  # free tier
        )
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)
    return pc.Index(INDEX_NAME)


def index_kb() -> int:
    """Chunk + embed the KB and upsert every chunk into Pinecone."""
    # 1. split the KB into chunks, then embed each chunk's text
    chunks = chunk_kb()
    vectors = embed_texts([c.text for c in chunks])
    index = get_index()
    # 2. build one record per chunk: id + its vector + metadata (text rides along)
    items = [
        {
            "id": c.chunk_id,
            "values": v,
            "metadata": {"source": c.source, "heading": c.heading or "", "text": c.text},
        }
        for c, v in zip(chunks, vectors)
    ]
    # 3. upsert in batches (Pinecone caps how many vectors per request)
    for i in range(0, len(items), 100):
        index.upsert(vectors=items[i:i + 100])
    return len(items)


def search(query: str, top_k: int = 3):
    """Embed the query and return the top_k nearest chunks from Pinecone."""
    index = get_index(create=False)
    # embed the query with the SAME model, then ask Pinecone for the nearest vectors
    qv = embed_texts([query])[0]
    res = index.query(vector=qv, top_k=top_k, include_metadata=True)
    return [(m["id"], m["score"], m["metadata"]["text"]) for m in res["matches"]]


if __name__ == "__main__":
    n = index_kb()
    print(f"indexed {n} chunks into Pinecone index '{INDEX_NAME}'")
    # Pinecone is eventually consistent — give the upsert a moment before querying.
    time.sleep(5)

    q = "my dashboard is blank and I think our google ads connector expired, how do I fix it?"
    print(f"\nQUERY: {q}\n")
    for rank, (cid, score, text) in enumerate(search(q), 1):
        print(f"  #{rank}  score={score:.3f}  [{cid}]")
        print("  " + text.replace("\n", " ")[:170])
