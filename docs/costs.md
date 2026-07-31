# Cost ledger — Polaris demo (GCP / Vertex AI)

Running record of API spend for this project. **Budget authorized: $100 USD (GCP
only, excludes MongoDB).**

> Figures are **estimates** from token counts × published rates — GCP billing is
> authoritative and lags ~a day. Rates used (Vertex, approx):
> `gemini-2.5-flash-lite` ≈ $0.10 / 1M input, $0.40 / 1M output ·
> `text-embedding-005` ≈ $0.0001 / 1K tokens.

| Date | Activity | Model | Volume | Est. USD |
|---|---|---|---|---|
| 2026-07-28 | KB chunk embeddings + RAG smoke tests | text-embedding-005 / haiku·flash-lite | ~90 chunks + few queries | ~$0.05 |
| 2026-07-29 | Ticket generation v2 (10 quarterly batches, incl. retries/smoke) | gemini-2.5-flash-lite | ~24k tickets | ~$3.00 |
| 2026-07-30 | Classifier feature embeddings | text-embedding-005 | 23,994 × 768 | ~$0.30 |
| **Spent to date** | | | | **≈ $3.35** |

## Pending (not yet incurred)

| Activity | Model | Volume | Est. USD |
|---|---|---|---|
| RAG answers for the UI — all `kb_autoresolve` | gemini-2.5-flash-lite | 14,089 answers | ~$2.54 |
| Escalation acknowledgments — **templated, no LLM** | — (Python templates) | 9,905 acks | ~$0.00 |

**Response strategy (cost-aware):** `kb_autoresolve` tickets (59%) get a grounded
**RAG answer** (LLM, ~$2.54 for all 14k, or cents for a curated sample). The other
9,905 escalate → a **templated acknowledgment** ("we've received your case and
routed it to the X team"), keyed by routing + sentiment tone — no LLM, ~$0. Use the
expensive tool only where it adds value; templates where they suffice.

## Running total

- **Spent: ≈ $3.35** of $100 (~3%).
- **Projected with full UI answers: ≈ $6** of $100.

Headroom is not the constraint — time is.

## Observed actual (real billing)

- **2026-07-30 — ~7,300 COP ≈ $1.80 USD** for the whole build to date (24k-ticket
  generation + a 1,398-response sample + all embeddings + live-path testing).
- Tracks the estimates and lands **under $2 for a complete end-to-end system**. The
  low figure is by design, not luck: Gemini/Flash-Lite where volume is high, **templated
  acks (no LLM) for escalations**, and exact cosine instead of a paid vector DB.
- Headline for interviews: *end-to-end synthetic-data + RAG + triage system, built for
  under $2.*
