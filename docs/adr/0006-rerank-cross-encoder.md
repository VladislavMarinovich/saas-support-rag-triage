# ADR-0006 — Rerank cross-encoder post-retrieval

- **Estado:** Rechazado para v2. Candidato a v2.1+.
- **Fecha:** 2026-08-18
- **Owner:** Vladislav Marinovich · Marinovich Consulting SAS
- **Refs:** [Constitution](../../.specify/memory/constitution.md) principios X (latency SLO p95 < 2s), VI (simple primero), XII (eval-driven). [POL-3 Spec](../../specs/001-polaris-v2/spec.md) sección 5 fuera de alcance. [ADR-0005](0005-fusion-rrf.md) — el retrieval híbrido con RRF es la etapa anterior a un potencial rerank.

## Contexto

En pipelines de RAG modernos es común agregar una etapa de **rerank** entre el retrieval y la generación. La idea: el retrieval (dense, BM25, o híbrido) devuelve un top-K amplio (K=20-50) de candidatos con precisión decente; un modelo más potente lee query + candidatos **juntos** y los reordena, refinando el top-5 final que se le pasa al LLM generador.

El modelo típico es un **cross-encoder** — entrena sobre pares (query, documento) y produce un score de relevancia. Ejemplos populares: `cross-encoder/ms-marco-MiniLM-L-12-v2` de sentence-transformers, o modelos comerciales como Cohere Rerank.

Este ADR documenta la decisión de **NO incluir rerank en v2** y las condiciones bajo las cuales se activaría en v2.1+.

## Opciones consideradas

**A. Rerank con cross-encoder self-hosted en el Worker (o service adjunto).** Bundlear un modelo pequeño (< 100 MB) o hostearlo como servicio separado (Modal, Fly.io, self-host). Cero costo por inferencia, control total. Requiere infra propia + optimización de latencia + mantenimiento del modelo.

**B. Rerank con API comercial (Cohere Rerank, Jina, Voyage).** Endpoint HTTPS que recibe query + candidatos y devuelve rankings. Cero infra propia. Costo por request (~$0.10 por 1000 requests típicamente). Latencia depende de la región del proveedor.

**C. Rerank con Vertex AI Reranker.** Si Google ofrece un servicio de rerank en Vertex, se mantendría dentro del stack single-cloud. Estado actual: revisar disponibilidad — puede que exista dentro de "Vertex AI Search" pero no como endpoint standalone.

**D. Skip rerank en v2.** Confiar en que RRF sobre top-N=20 de cada método produce un top-5 suficientemente bueno para el generador.

## Decisión

**Opción D: NO incluir rerank en v2.**

Se aplaza la decisión a v2.1+ contingente a evidencia empírica del eval framework (POL-10) y del dashboard en producción.

## Justificación

**Argumentos contra rerank en v2:**

1. **Latencia significativa.** Un cross-encoder típico sobre top-20 candidatos añade 200–500 ms al path completo. El SLO de v2 es p95 < 2 s (Principio X). Sin baseline concreto de dónde está la latencia hoy, agregar 300 ms de rerank sin datos es ruleta — puede llevar el p95 sobre el umbral y activar un rediseño en emergencia.

2. **Beneficio marginal desconocido.** Rerank aporta cuando el retrieval de base es débil o cuando el orden dentro del top-K importa mucho (por ejemplo, precisión@1 crítica). Para RAG grounded donde el LLM recibe top-5 y genera respuesta considerando todos, el orden dentro del top-5 tiene menos peso — un chunk relevante en posición 3 se lee igual que uno en posición 1.

3. **Complejidad de infra.** Cualquier opción (A, B, C) agrega superficie: self-host es mantenimiento; API comercial es dependencia externa y costo variable; Vertex Reranker (si existe) requiere validación de disponibilidad y contratos.

4. **Principio VI (simple primero).** RRF sobre hybrid es la base más simple que puede funcionar. Se mide su desempeño; si es suficiente, no se agrega rerank.

5. **Riesgo de sobre-ingeniería.** Similar al caso descartado en ADR-0004 (canonicalize morfológico), agregar rerank sin evidencia de que RRF se queda corto es diseñar contra fantasmas. El eval framework (POL-10) es el árbitro.

**Argumentos a favor de reevaluar en v2.1+:**

Rerank tiene sentido cuando se cumplen simultáneamente:

- El eval framework muestra que RRF alcanzó un plateau claro y hay gap contra un baseline hipotético con oráculo.
- El dashboard muestra que hay margen sustancial de latencia (p95 actual < 1.4 s, dejando 600 ms de headroom).
- Hay evidencia de queries reales donde el top-1 del RRF no era el mejor chunk según el LLM (medible con feedback implícito: el LLM cita más el chunk en posición 3 que el chunk en posición 1).

## Consecuencias

**Positivas (de no incluirlo):**

- Latencia predecible, dentro del SLO holgadamente.
- Cero infra nueva, cero dependencia adicional.
- Cero costo variable por rerank.
- Path de código más simple; menos cosas que pueden fallar.
- Alineado con Principio VI.

**Negativas (potenciales, no observadas):**

- Si hay queries donde el orden intra-top-5 importa, podríamos estar dejando calidad sobre la mesa. Métricas de vigilancia lo detectan.
- Reviewers USD sofisticados podrían preguntar por qué no incluimos rerank — respuesta lista: decisión eval-driven documentada aquí, criterios de activación explícitos.

## Métricas de vigilancia

| SLI (campo del schema BQ + widget dashboard) | Umbral que dispara reevaluación | Acción |
|---|---|---|
| **`rrf_plateau_indicator`** — delta de Recall@5 entre POL-10 eval trimestre-a-trimestre. Si RRF no mejora con expansiones de KB o ajustes de N, indica plateau. Widget: time series trimestral. | Delta trimestral < 1 punto porcentual durante 2 trimestres consecutivos. | Reabrir ADR-0006. Evaluar rerank con eval controlado antes de decisión. |
| **`retrieval_latency_p95`** — mismo SLI de ADR-0005. | p95 < 1200 ms sostenido durante 30 días (hay headroom). | Habilitar condición necesaria para evaluar rerank. No dispara acción por sí sola. |
| **`top1_citation_ratio`** — porcentaje de respuestas del LLM que citan el chunk en posición 1 del top-5. Widget: stat. Si el LLM cita consistentemente chunks en posiciones 3-5 más que el top-1, indica que el orden del RRF no está alineado con lo que el LLM necesita. | Ratio < 40% durante 60 días con muestra > 1000 queries. | Rerank pasa de candidato a prioridad para v2.1. Abrir POL-XX historia dedicada. |

## Cuándo revisitar este ADR

- Cualquiera de las tres métricas de vigilancia arriba dispara acción.
- Aparece un modelo cross-encoder específicamente entrenado para RAG multilingüe que hace la latencia trivial (< 50 ms para top-20).
- Cambio en Constitution que altere el SLO de latencia (por ejemplo, si el producto se posiciona en un vertical donde 3 s es aceptable).

## Referencias

- Cross-encoders para retrieval, sentence-transformers: [sbert.net/examples/applications/retrieve_rerank/README.html](https://www.sbert.net/examples/applications/retrieve_rerank/README.html).
- Cohere Rerank API: [docs.cohere.com/docs/rerank-overview](https://docs.cohere.com/docs/rerank-overview).
- ADR-0005 (RRF) — la etapa anterior; rerank sería complemento posterior.
