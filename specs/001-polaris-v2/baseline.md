# Baseline v1 — retrieval dense-only (POL-10, subtarea 10.4)

**Este documento es el gate de v2** (Principio XII, eval-driven): su publicación desbloquea 6.1, 7.1, 9.1 y 11.1. Todo PR de implementación de v2 adjunta la salida del eval con delta contra ESTOS números; un PR que degrade Recall@5 o MRR en los casos donde v1 acertaba se justifica por escrito o se rechaza (eval.md §7).

**Fecha:** 2026-08-21 · **Config:** v1 dense-only · **Corpus:** v1 (47 queries) · **KB:** 52 chunks

## Métricas globales

| Métrica | v1 (dense-only) |
|---|---|
| Recall@1 | 0.70 |
| Recall@5 | 0.92 |
| Precision@5 | 0.31 |
| MRR | 0.80 |
| p50 retrieval (ms) | 176 |
| p95 retrieval (ms) | 498 |
| Costo/query | $0.0000002 |
| answer_type match | 6/10 |

Sobre 37 queries con chunk esperado; las 10 sin chunk esperado (fuera de dominio y ambiguas sin respuesta defendible) se evalúan solo por answer_type (umbral empírico `top1_score < 0.50`, discovery §4).

## Por idioma

| Grupo | n | Recall@1 | Recall@5 | Precision@5 | MRR |
|---|---|---|---|---|---|
| en | 17 | 0.71 | 0.88 | 0.28 | 0.79 |
| es | 20 | 0.70 | 0.95 | 0.34 | 0.80 |

Sin sesgo severo entre idiomas (criterio Spec §6): ES y EN quedan a ≤ 0.07 en todas las métricas.

## Por categoría

| Grupo | n | Recall@1 | Recall@5 | Precision@5 | MRR |
|---|---|---|---|---|---|
| ambigua | 1 | 1.00 | 1.00 | 0.60 | 1.00 |
| tipica | 29 | 0.79 | 0.97 | 0.33 | 0.87 |
| typo_jerga | 7 | 0.29 | 0.71 | 0.20 | 0.46 |

## answer_type — el «no sé» honesto

| ID | Categoría | top1_score | ¿gatilla el umbral 0.50? |
|---|---|---|---|
| amb-01 | fuera_de_dominio | 0.383 | sí |
| amb-03 | ambigua | 0.469 | sí |
| amb-04 | ambigua | 0.455 | sí |
| amb-05 | fuera_de_dominio | 0.371 | sí |
| ec-01 | fuera_de_dominio | 0.601 | NO |
| ec-02 | fuera_de_dominio | 0.415 | sí |
| ec-03 | fuera_de_dominio | 0.676 | NO |
| man-11 | ambigua | 0.553 | NO |
| man-13 | fuera_de_dominio | 0.690 | NO |
| man-14 | fuera_de_dominio | 0.477 | sí |

## Lectura del baseline (dónde pierde v1)

1. **typo/jerga es el punto débil claro** (Recall@1 0.29, MRR 0.46 vs 0.87 de las típicas). Las **únicas 3 queries que ni siquiera llegan al contexto** (Recall@5 = 0) son de término exacto: `typo-03` (reautorizar oauth), `typo-04` (api key rotation) y `amb-02` (TikTok Ads — la KB la responde y el denso no la ve). Es exactamente la apuesta de POL-7 (BM25 + RRF): el delta esperado de v2 vive acá.
2. **El umbral 0.50 funciona para lo claramente ajeno, no para lo cercano al dominio**: gatilla en 6/10 (vuelos, Bitcoin, "help"), pero falla en los códigos de error `ec-01`/`ec-03` (score 0.60-0.68: el denso encuentra chunks de sync/reports "parecidos" y respondería con falsa confianza) y en `man-11`/`man-13`. Dato directo para POL-11 (artículos de códigos) y para la calibración del "no sé" en POL-9.
3. **Fallas de Recall@1 con acierto en top-5** (8 casos, MRR 0.25-0.50): el chunk correcto llega al prompt pero no de primero — mejorable por re-ranking (RRF de POL-7) sin tocar la KB.

## Config exacta y reproducibilidad

- **Config:** v1 (dense-only) — embed Vertex + cosine exacto in-memory, sin BM25 ni RRF
- **KB:** 52 chunks (chunker discovery `source::heading`) · hash índice `a0cd72dab0ef`
- **Corpus:** v1 (47 queries) · sha `e93d63672084` · `src/eval/corpus/corpus.jsonl`
- **Embeddings:** `text-embedding-005` (Vertex) · top-K = 5
- **Comando:** `uv run python -m src.eval.run --config v1 --fecha 2026-08-21`
- **Determinismo verificado:** el eval se corrió DOS veces; reportes byte-idénticos (`diff` vacío). Los embeddings quedaron congelados en `src/eval/cache/` — re-correr cuesta USD 0.
- **Costo real del experimento:** USD 0.00015 (99 embeddings: 52 chunks KB + 47 queries; el segundo run costó $0.00000).
- **Latencia:** percentiles del embed de query (Vertex, congelados en cache en el primer run); el cosine in-memory agrega < 1 ms (medido en consola) y no entra al reporte por determinismo.
