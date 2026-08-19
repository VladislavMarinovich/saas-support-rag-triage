# ADR-0004 — Tokenización de BM25 para retrieval híbrido multilingüe

- **Estado:** Aceptado
- **Fecha:** 2026-08-18
- **Owner:** Vladislav Marinovich · Marinovich Consulting SAS
- **Refs:** [Constitution](../../.specify/memory/constitution.md) principios VI (simple primero — cache antes de compute), XIV (multilingual by default), XII (eval-driven). [POL-3 Spec](../../specs/001-polaris-v2/spec.md) sección 3 feature Retrieval híbrido (POL-7) y sección 7 riesgo BM25 stemmer-less. [ADR-0001](0001-cache-backend.md) — mismo diseño de simplicidad primero.

## Contexto

v2 introduce retrieval híbrido: candidatos por índice denso (embeddings) + candidatos por índice léxico (BM25 sobre los mismos chunks) fusionados con Reciprocal Rank Fusion (RRF). BM25 requiere una decisión concreta sobre cómo tokenizar el texto — cortarlo en unidades para indexar y para hacer match.

La decisión no es trivial porque el sistema es multilingüe (Principio XIV): la KB puede contener chunks en varios idiomas y los queries llegan en distintos idiomas. Cada idioma tiene morfología distinta — español conjuga verbos y pluraliza sustantivos con flexiones ricas, inglés casi no, alemán compone palabras compuestas largas, chino no separa palabras con espacios.

Un stemmer (algoritmo que reduce palabras a su raíz — `casas` → `cas`, `corriendo` → `corr`) mejora recall en idiomas flexivos pero es específico por idioma. Sin stemmer, `casa` y `casas` no matchean y se pierde recall. Con el stemmer equivocado (español aplicado a inglés) se rompen matches y se pierde precisión.

## Opciones consideradas

**A. Stemmer per-idioma en el pipeline.** Detectar idioma del query y del chunk → aplicar stemmer específico (Snowball para español, Porter para inglés, etc). Máximo recall por idioma. Requiere: librería multi-stemmer bundleable en Cloudflare Worker (ej. `snowball-js`), detección confiable de idioma, mantenimiento de mapeo idioma→stemmer.

**B. Stemmer-less puro.** Tokenización simple whitespace + normalización unicode NFKC + lowercase + eliminación de puntuación. Ningún stemmer. Recall degrada por variantes flexionales en idiomas ricos, pero funciona igual para cualquier idioma sin lógica condicional.

**C. Canonicalización morfológica delegada a canonicalize (POL-6) + BM25 stemmer-less.** El LLM del paso de canonicalize normaliza morfológicamente la query y también los chunks al indexar offline. BM25 opera sobre formas ya normalizadas. Elegante pero considerado y **descartado**: contradice el diseño del hybrid retrieval, donde dense y BM25 son deliberadamente complementarios. Convertir BM25 en un casi-dense elimina la razón de ser del hybrid.

## Decisión

**Opción B: BM25 stemmer-less puro para v2.**

Tokenización:
- Normalización unicode NFKC (unifica formas equivalentes de un mismo caracter).
- Lowercase.
- Split por whitespace y separadores de puntuación (`, . ; : ! ? ( ) [ ] { } " ' /`).
- Filtrado de tokens vacíos.
- Sin stopwords en v2 (se evalúa si el eval sugiere valor).
- Sin stemming.

## Justificación

El hybrid retrieval (BM25 + dense fusionados por RRF) está **diseñado precisamente** para que cada método cubra las debilidades del otro:

- **Dense (embeddings)** captura variantes flexionales, sinónimos y contexto semántico. `casas registradas` y `casa registrada` viven cerca en el espacio de embeddings porque significan lo mismo. `text-embedding-005` es multilingüe nativo — resuelve morfología sin lógica adicional del sistema.
- **BM25** captura términos exactos: nombres de features, jerga interna, códigos, siglas. Casos donde dense se pierde.

Si BM25 stemmer-less pierde recall por flexión, dense lo compensa. Si dense se pierde por término exacto, BM25 lo compensa. RRF (k=60) los fusiona: un chunk en top-5 de cualquiera de los dos aparece en el top-K final.

Tratar de resolver el problema de morfología dentro de BM25 (opción A) o pre-procesando con LLM (opción C) es **combatir contra el diseño del hybrid**. Es sobre-ingeniería que viola Principio VI (simple primero).

## Consecuencias

**Positivas:**

- Código simple: un tokenizador genérico, sin lógica per-idioma.
- Cero mantenimiento de mapeo idioma→stemmer.
- Cero dependencias externas nuevas en el Worker (no hay que bundlear `snowball-js`).
- Coherente con hybrid retrieval como diseño: cada método hace su parte.
- Reversible: si eval muestra un idioma específico degradado, se activa stemmer solo para ese idioma sin afectar a los demás.

**Negativas / trade-offs aceptados:**

- BM25 individual tiene recall menor en idiomas flexivos ricos (español, alemán, ruso, árabe) que uno con stemmer. Aceptado porque **el recall final es del hybrid, no del BM25 solo**.
- Sin stopword removal, tokens comunes (`el`, `la`, `de`, `the`, `a`, `and`) generan matches ruidosos con score bajo. BM25 ya penaliza términos frecuentes con su factor IDF; el ruido residual es menor y se resuelve en RRF. Se reevalúa si POL-10 sugiere que ayuda.

## Métricas de vigilancia

Cada ADR de aquí en adelante ata su decisión a métricas concretas del dashboard y umbrales que disparan acción. Este es el estándar del proyecto — un ADR sin métricas de vigilancia es un documento muerto.

Para ADR-0004:

| SLI (campo del schema BQ y widget del dashboard) | Umbral que dispara reevaluación | Acción |
|---|---|---|
| **`bm25_recall_at_5_by_language`** — recall@5 de BM25 solo (antes de fusión RRF), segmentado por `query_lang_detected`. Widget: bar chart. | Recall@5 de un idioma específico cae bajo 40% durante 7 días consecutivos con muestra estadísticamente significativa (mínimo 200 queries en ese idioma en la ventana). | Activar stemmer específico para ese idioma. Abrir ADR-0004-b documentando qué idioma y por qué. |
| **`hybrid_recall_at_5`** — recall@5 del hybrid completo (después de RRF). Widget: gauge. | Recall@5 hybrid cae bajo 65% globalmente durante 7 días. | Reabrir todo el diseño de retrieval (ADR-0004 y ADR-0005 juntos). No aislar cambios. |
| **`bm25_dense_agreement_rate`** — porcentaje de queries donde BM25 y dense retornan al menos 1 chunk en común en el top-5. Widget: time series. | Agreement rate < 10% durante 30 días. | Investigar por qué los dos métodos ven cosas tan distintas. Puede indicar chunks mal dimensionados (revisar chunking) o KB heterogénea (revisar tipos de contenido). |
| **`kb_coverage_pct`** — porcentaje de chunks distintos vistos al menos una vez como top-K sobre ventana móvil 7 días. Se calcula como `count(distinct top1_source \|\| '::' \|\| top1_heading) / total_chunks_kb`. Widget: gauge. | < 60% durante 30 días con muestra > 500 queries. | Auditar chunks huérfanos. Descubrimiento empírico Fase 0.b: 13/52 chunks (25%) no aparecieron nunca en top-3 sobre 30 queries — posibles causas incluyen sesgo del corpus, embeddings genéricos que ninguna query natural activa, o chunking demasiado fino que fragmenta contenido buscable. Antes de expandir KB (POL-11), diagnosticar. |

Estos SLIs se derivan del eval framework (POL-10) corriendo periódicamente sobre el corpus etiquetado más el tráfico real de producción segmentado.

## Referencias

- BM25 (Okapi): [en.wikipedia.org/wiki/Okapi_BM25](https://en.wikipedia.org/wiki/Okapi_BM25).
- Reciprocal Rank Fusion (Cormack et al., 2009): usado como estándar de fusión en RAG modernos por su robustez y falta de hiperparámetros por tuning.
- Snowball stemmers (si se activa alguno en el futuro): [snowballstem.org](https://snowballstem.org).
- ADR-0005 (siguiente) — cómo se hace la fusión de rankings.
