# ADR 0001 — Retrieve with brute-force cosine over MongoDB, not a dedicated vector DB

- **Status:** Accepted
- **Date:** 2026-07-30
- **Decision owner:** Vlad Marinovich

## Context

The RAG assistant retrieves from a **small, static knowledge base: 90 chunks**
(~370-token articles, section-level). The first build used **Pinecone** (a managed
vector DB) for retrieval, alongside **MongoDB** as the application store (tickets +
responses) and **Vertex AI** for embeddings.

For a corpus this size, a dedicated vector DB adds an external service, a second
secret, and a network hop — with no measurable benefit. An early benchmark made
this concrete: exact **in-memory cosine similarity matched Pinecone almost exactly**
(top hit **0.824 in-memory vs 0.825 Pinecone**). The retrieval quality is identical;
Pinecone was only carrying operational complexity.

A portfolio-facing demo is also judged on **right-sizing**: three external data
services for a KB that fits in memory reads as resume-driven over-engineering, not
sound design.

## Decision

**Remove the dedicated vector DB (Pinecone).** Store the KB chunks *and* their
embeddings in **MongoDB** (the single system-of-record), and retrieve with **exact
brute-force cosine** (top-k) computed in the app. Embeddings continue to come from
the Vertex AI embedding API (an inherent external call, not an infrastructure
layer).

Resulting stack: **MongoDB** (tickets · KB chunks · vectors · responses) +
**embedding API** + **LLM API**. One database, no separate vector store.

## Consequences / trade-offs

**Positive**
- Simpler architecture: one datastore, one fewer vendor and secret to manage.
- Free-tier clean: MongoDB **M0 is free forever** and easily holds the data; no
  paid-tier or promotional-credit cliff.
- **Exact** retrieval (not approximate) — at this scale it is also instant (µs).
- Demonstrates judgment: the minimal stack that does the job.

**Negative / limits**
- Brute-force cosine is **O(n·d) per query** — fine at 90 vectors, but it does
  **not scale**. Past roughly tens of thousands of vectors, latency and cost demand
  an approximate-nearest-neighbour index.
- Less hands-on surface with a managed vector DB *in this repo* (mitigated by this
  ADR documenting exactly when one is warranted).

## When we would revisit

Introduce a vector index (**MongoDB Atlas Vector Search** to stay single-platform,
or **Pinecone** for a dedicated store) when **any** of these hold:

- the KB grows past ~10k–100k chunks, or
- p99 retrieval latency becomes user-visible, or
- we need metadata-filtered ANN at scale.

Until then, exact cosine is the correct tool. *Use a vector DB when the corpus earns
it — not before.*
