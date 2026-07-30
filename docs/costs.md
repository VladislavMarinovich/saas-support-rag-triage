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
| RAG answers for the UI — curated sample | gemini-2.5-flash-lite | ~400 answers | ~$0.07 |
| RAG answers for the UI — all `kb_autoresolve` | gemini-2.5-flash-lite | 14,089 answers | ~$2.54 |

**Only `kb_autoresolve` tickets (59%) get a RAG answer; the other 9,905 escalate
(routed to a team, no generated answer).** Answering the full deflectable set costs
~$2.54; a curated sample for the gallery, cents.

## Running total

- **Spent: ≈ $3.35** of $100 (~3%).
- **Projected with full UI answers: ≈ $6** of $100.

Headroom is not the constraint — time is.
