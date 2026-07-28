"""RAG answering: retrieve KB chunks, then let the LLM answer grounded — or
refuse honestly when the chunks don't actually answer the question.

This is the two-layer honesty:
  1. retrieval (Pinecone) brings the nearest chunks — a weak pre-filter.
  2. the LLM reads them and JUDGES whether they answer the question; if not, it
     admits Polaris doesn't cover it instead of inventing.
"""

from __future__ import annotations

from src.vectorstore import search
from src.llm import generate

PROMPT = """You are a support assistant for Polaris, an analytics SaaS. Answer the \
customer's question using ONLY the knowledge-base excerpts provided.

Rules:
- If the excerpts answer the question, reply concisely and helpfully, grounded only in them.
- If the excerpts do NOT answer it — or it asks about something Polaris does not do — \
say so honestly (e.g. "I don't have information about that" or "Polaris doesn't support \
that"). Never invent features or steps.
- Answer naturally; do not mention "excerpts" or "context".

Knowledge-base excerpts:
{context}

Customer question: {question}

Answer:"""


def answer(question: str, top_k: int = 3):
    """Retrieve top_k chunks and return (llm_answer, hits)."""
    # 1. retrieve the most relevant KB chunks for the question
    hits = search(question, top_k=top_k)
    # 2. stitch those chunks into a single context block for the prompt
    context = "\n\n".join(f"[{cid}] {text}" for cid, _score, text in hits)
    # 3. LLM answers grounded in that context — or refuses if it doesn't fit
    reply = generate(PROMPT.format(context=context, question=question), max_tokens=400)
    return reply, hits


if __name__ == "__main__":
    questions = [
        "How do I connect HubSpot to Polaris?",   # in-scope -> grounded answer
        "Can Polaris book my flights?",           # out-of-scope -> honest refusal
        "Do you support TikTok Ads?",             # borderline -> should refuse
    ]
    for q in questions:
        reply, hits = answer(q)
        top = hits[0]
        print("=" * 72)
        print(f"Q: {q}")
        print(f"(top retrieval: {top[1]:.3f} [{top[0]}])")
        print(f"A: {reply.strip()}")
        print()
