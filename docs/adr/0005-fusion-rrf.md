# ADR-0005 — Fusión de rankings de retrieval híbrido

- **Estado:** Aceptado
- **Fecha:** 2026-08-18
- **Owner:** Vladislav Marinovich · Marinovich Consulting SAS
- **Refs:** [Constitution](../../.specify/memory/constitution.md) principios VI (simple primero), X (latency SLO), XII (eval-driven). [POL-3 Spec](../../specs/001-polaris-v2/spec.md) sección 3 feature Retrieval híbrido (POL-7). [ADR-0004](0004-bm25-tokenizacion.md) — BM25 estemer-less complementa a dense; la fusión es donde se materializa la complementariedad.

## Contexto

El retrieval híbrido de Polaris v2 produce dos rankings paralelos por cada query:

- Un ranking léxico de BM25 sobre el índice invertido de chunks.
- Un ranking denso por similitud coseno entre el embedding de la query y los embeddings de los chunks (`text-embedding-005`).

Los dos rankings devuelven listas ordenadas de chunks con scores en escalas incomparables — BM25 puede dar valores desde 0 hasta > 20, dense da similitudes coseno entre -1 y 1. Un chunk típicamente aparece en ambos rankings pero en posiciones distintas.

El problema es cómo **fusionar** los dos rankings en uno solo que use lo mejor de cada método sin sesgarse por escalas de score incompatibles.

## Opciones consideradas

**A. Weighted linear combination.** `score_final = w1 * norm(score_BM25) + w2 * norm(score_dense)`. Requiere normalizar cada score al rango [0,1] (min-max o z-score) y tunear los pesos `w1, w2`. Frágil: la normalización depende del batch, los pesos óptimos dependen del corpus y del dominio, y hay que re-tunear cada vez que cambia la KB.

**B. CombSUM / CombMNZ.** Familia clásica de fusión pre-RRF. Suma scores normalizados con variantes. Superada por RRF en la mayoría de benchmarks. Aún requiere normalización.

**C. Reciprocal Rank Fusion (RRF) con k=60.** No usa scores, solo posiciones (rank). Para cada chunk: `score_RRF = Σ 1 / (k + rank_en_método_i)`. Robusto, no requiere normalización ni tuning por dataset. `k=60` es la constante empírica estándar propuesta por Cormack et al. (2009).

**D. Learning-to-rank (LTR).** Modelo de ML entrenado con queries etiquetadas + rankings óptimos. Máxima calidad si hay data suficiente. Requiere pipeline de entrenamiento, monitoreo de drift y data etiquetada — todo trabajo separado y significativo. Fuera del scope de v2 (candidato v2.1+).

**E. Rerank cross-encoder** entre dense + BM25 y el resultado. Distinto problema — rerank es una capa post-fusión que reordena los top-K. Se decide en su propio ADR (0006). No sustituye la fusión, la complementa.

## Decisión

**Opción C: Reciprocal Rank Fusion con k=60.**

### Fórmula

Para cada chunk que aparece en al menos uno de los dos rankings de retrieval:

```
score_RRF(chunk) = 1 / (60 + rank_BM25(chunk)) + 1 / (60 + rank_dense(chunk))
```

Si un chunk no aparece en el top-K de un método, su contribución de ese método es 0. Se ordenan por `score_RRF` descendente y se toma el top-K final (K típicamente 5–8 chunks que se pasan al LLM generador).

### Justificación del `k=60`

- Sin `k` (o `k=0`), la contribución cae rápido con la posición: rank 1 contribuye 1.0, rank 2 contribuye 0.5, rank 3 contribuye 0.33. El top-1 domina y aplasta el consenso.
- Con `k=60`, la contribución es plana pero decreciente: rank 1 contribuye 0.0164, rank 2 contribuye 0.0161, rank 3 contribuye 0.0159. Diferencias pequeñas entre posiciones cercanas. Un chunk que aparece en top-3 de ambos métodos gana a un chunk que aparece top-1 de un solo método.
- Cormack et al. probaron `k` entre 0 y 200 empíricamente y `k=60` dio el mejor rendimiento promedio en múltiples benchmarks IR. Es el estándar adoptado por la mayoría de sistemas RAG modernos.
- Cambiar `k` requiere re-evaluar con datos propios. Beneficio marginal esperado bajo comparado con el costo de tuning y mantenimiento.

## Diseño operativo

1. BM25 devuelve top-N candidatos (N = 20).
2. Dense devuelve top-N candidatos (N = 20).
3. Se hace RRF sobre la unión de los dos conjuntos (~30–40 chunks distintos típicamente).
4. Se ordenan por `score_RRF` descendente.
5. Se toma top-K final (K = 5 para el prompt de generación, ajustable).

N=20 por método es un compromiso: suficientemente grande para que ambos métodos aporten diversidad al consenso, suficientemente chico para no explotar la memoria del Worker ni el tiempo de fusión (que es lineal en N).

## Consecuencias

**Positivas:**

- Cero tuning de hiperparámetros específico al corpus. Cambiar la KB no rompe la fusión.
- Cero dependencia de normalización de scores (evita sesgo por outliers).
- Estándar de industria — reviewers USD reconocen el algoritmo por nombre.
- Implementación trivial: ~15 líneas de código en JS puro. Sin librería externa.
- Combina bien con la filosofía de retrieval híbrido — recompensa consenso, no dominancia.

**Negativas / trade-offs aceptados:**

- Descarta señal fina de los scores. Un chunk que BM25 rankea top-1 con score sobresaliente (evidencia fortísima) contribuye lo mismo que otro top-1 con score marginal. Aceptado: el ruido de normalizar scores incomparables suele hacer más daño que el beneficio de aprovecharlos.
- `k=60` es constante fija. Si un dominio muy específico se beneficia de otra `k`, no se detecta hasta que el eval framework lo sugiera. Métricas de vigilancia lo cubren.

## Métricas de vigilancia

| SLI (campo del schema BQ + widget dashboard) | Umbral que dispara reevaluación | Acción |
|---|---|---|
| **`rrf_lift_over_dense_only`** — delta de Recall@5 del hybrid con RRF vs dense solo. Positivo indica que la fusión aporta. Widget: stat con delta absoluto. | Delta < 3 puntos porcentuales durante 14 días con muestra > 500 queries. | Reabrir ADR-0005. Evaluar si RRF está agregando ruido o si el problema es BM25 (revisar ADR-0004). |
| **`top1_agreement`** — porcentaje de queries donde el chunk top-1 del RRF coincide con el top-1 de al menos un método individual. Widget: gauge. | Agreement < 40% durante 30 días. | Investigar por qué RRF está eligiendo consistentemente chunks que ningún método individual priorizó. Puede indicar bug en la implementación o problema profundo con la complementariedad. |
| **`retrieval_latency_p95`** — latencia p95 del bloque retrieval completo (BM25 + dense + RRF). Widget: time series con banda de SLO. | p95 > 400 ms durante 7 días. | Reducir N (top-N por método) de 20 a 15 o migrar BM25 a estructura más eficiente. |

## Referencias

- Cormack, Clarke & Büttcher (2009), "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods". SIGIR. [Paper original](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf).
- ADR-0004 (BM25 stemmer-less) — la fuente del ranking léxico.
- ADR-0006 (rerank) — complemento post-fusión evaluado por separado.
