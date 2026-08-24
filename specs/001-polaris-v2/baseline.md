# Baseline v1 — retrieval dense-only

> ## ⛔ PENDIENTE DE FIRMA DE VLAD — este documento NO está vigente todavía
>
> Re-estampar el baseline es **una de las tres fronteras declaradas** de la Constitución v1.1.0 (Flujo de Trabajo, "autonomía en el medio, gate en las fronteras"): es el instrumento de medición contra el que se compara toda afirmación de mejora de v2, así que cambiarlo cambia la vara. El ejecutor de 11.5 dejó los números medidos y la evidencia escrita; **la vigencia la declara Vlad al firmar**, después de ver estos números.
>
> **Mientras no haya firma, el baseline vigente sigue siendo la corrida del 2026-08-21** (conservada íntegra al final de este documento).

**Este documento es el gate de v2** (Principio XII, eval-driven). Todo PR de implementación de v2 adjunta la salida del eval con delta contra los números de la sección vigente; un PR que degrade Recall@5 o MRR en los casos donde v1 acertaba se justifica por escrito o se rechaza ([eval.md](../../docs/features/eval.md) §7).

---

## 1. Por qué se re-estampa: el instrumento cambió dos veces

`kb-expansion.md` §6 previó este re-estampado y aceptó su costo ("el gate se re-estampa una vez; es preferible a arrastrar un asterisco permanente en la tabla comparativa de v2"). Los dos cambios son independientes y hay que separarlos para leer los números:

| # | Cambio | Qué movió | Dónde está la evidencia |
|---|---|---|---|
| 1 | **Índice del eval saneado** (11.4) | 52 → **184 chunks**: +18 secciones recuperadas (el chunker viejo borraba la última sección de 18 de los 20 artículos) y −2 chunks de puro footer. **Cero ids perdidos.** | `kb-audit.md` §3 · hallazgos 11.4 |
| 2 | **KB expandida** (11.3 + 11.4 bis) | 20 → **75 artículos**. En producción, `worker/kb_vectors.json` pasó de 90 a **261 chunks**. | `kb-expansion.md` · hallazgos 11.3 / 11.4 bis |

**El cambio #1 es el que más movió los números, y no es una degradación del sistema: es que el instrumento dejó de estar roto.** 7 de las 9 queries que perdieron el top-1 lo perdieron ante una sección **recuperada del mismo artículo** — chunks que no existían en el índice cuando se escribieron las etiquetas. Solo 2 lo perdieron ante un artículo nuevo.

Además, **las etiquetas del corpus se revisaron** (obligación de `eval.md` §2 al expandir la KB): 9 queries re-etiquetadas, **13 chunk_ids agregados, 0 eliminados**, con justificación por contenido chunk por chunk en `bitacora/hallazgos.md` (entrada 11.5). Las tres queries de término exacto `typo-03`, `typo-04` y `amb-02` quedaron **intactas y fallando a propósito**: son la apuesta que POL-7 (BM25 + RRF) debe ganar y su valor está en fallar hoy.

---

## 2. Baseline propuesto — 2026-08-24

**Config:** v1 dense-only · **Corpus:** 115 queries (**47 del baseline** + 68 `post_baseline`) · **KB:** 184 chunks (hash `11eef1a591ae`)

### 2.1 Población del baseline — la única comparable

| Métrica | v1 (dense-only) |
|---|---|
| Recall@1 | 0.62 |
| Recall@5 | 0.90 |
| Precision@5 | 0.32 |
| MRR | 0.74 |
| p50 retrieval (ms) | 176 |
| p95 retrieval (ms) | 498 |
| Costo/query | $0.0000002 |
| answer_type match | 5/7 |

Sobre **40 queries con chunk esperado**; las 7 sin chunk esperado se evalúan solo por answer_type. La población pasó de 37+10 a 40+7 porque `ec-01/02/03` se re-etiquetaron de `fuera_de_dominio` a `grounded` en 11.3 — **ese cambio de etiqueta ES la medición de que la expansión sirvió** (`kb-expansion.md` §7).

### 2.2 Comparación estricta contra el baseline del 21-ago (las MISMAS 37 queries)

Para que la comparación sea de manzanas con manzanas, se excluyen `ec-01/02/03` de ambos lados:

| Métrica | 21-ago (52 chunks) | **24-ago (184 chunks, etiquetas revisadas)** | Δ |
|---|---|---|---|
| Recall@1 | 0.70 | **0.59** | **−0.11** |
| Recall@5 | 0.92 | **0.89** | **−0.03** |
| Precision@5 | 0.31 | **0.32** | +0.01 |
| MRR | 0.80 | **0.73** | **−0.07** |

### 2.3 Estado de la no-regresión: FALLA, y se documenta como falla

`eval.md` §7 y `kb-expansion.md` §7 exigen Recall@5 y MRR sin degradación donde v1 acertaba. **No se cumple.** No se maquilla y no se pide excepción; se declara con su causa:

- **Recall@5 −0.03 = una sola query.** `typo-05` («dashboards no cargan tras cambio plan») perdió el top-5 que tenía. Se revisó chunk por chunk el nuevo top-5 y **ninguno responde la pregunta**, así que la etiqueta no se tocó. Es degradación real. Es también una query de término exacto ("cambio plan"), así que cae del mismo lado de la apuesta de POL-7.
- **Las 4 queries con Recall@5 = 0 son `typo-03`, `typo-04`, `typo-05` y `amb-02`.** Tres estaban ya fallando en el baseline del 21-ago por diseño; la cuarta es `typo-05`. Las cuatro son de término exacto: **el punto de fuga de v1 quedó todavía más nítido que en el baseline anterior**, y es exactamente donde v2 tiene que mostrar su delta.
- **Recall@1 −0.11 y MRR −0.07** los explica el saneamiento del índice: secciones que llevaban invisibles desde el discovery ahora compiten por el top-1 del mismo artículo. El chunk correcto sigue llegando al contexto del LLM (Recall@5 0.89), pero deja de ser el primero. Es un problema de **ranking**, que es literalmente lo que RRF de POL-7 existe para arreglar (lectura 3 del baseline anterior, hoy más grande).

**Qué NO justifica esta caída:** no se aceptó ni un solo cambio de etiqueta cuyo argumento fuera la métrica. De los 13 chunk_ids agregados, **8 no mueven ninguna métrica** y uno solo convierte una falla de Recall@5 en acierto (`man-10`, justificado por el contenido del chunk, ver hallazgos 11.5).

### 2.4 Por idioma

| Grupo | n | Recall@1 | Recall@5 | Precision@5 | MRR |
|---|---|---|---|---|---|
| en | 18 | 0.56 | 0.89 | 0.30 | 0.70 |
| es | 22 | 0.68 | 0.91 | 0.34 | 0.78 |

Sin sesgo severo entre idiomas (criterio Spec §6): la mayor brecha es 0.12 en Recall@1, a favor del español — el baseline anterior tenía 0.07 a favor del inglés. Ninguna métrica muestra un idioma sistemáticamente peor.

### 2.5 Por categoría

| Grupo | n | Recall@1 | Recall@5 | Precision@5 | MRR |
|---|---|---|---|---|---|
| ambigua | 1 | 1.00 | 1.00 | 0.40 | 1.00 |
| tipica | 32 | 0.69 | 0.97 | 0.35 | 0.81 |
| typo_jerga | 7 | 0.29 | 0.57 | 0.17 | 0.39 |

`typo_jerga` sigue siendo el punto débil y empeoró (Recall@5 0.71 → 0.57): 4 de sus 7 queries no llegan al contexto.

### 2.6 answer_type — el «no sé» honesto (umbral `top1_score < 0.50`)

| ID | Categoría | top1_score | ¿gatilla el umbral 0.50? |
|---|---|---|---|
| amb-01 | fuera_de_dominio | 0.433 | sí |
| amb-03 | ambigua | 0.490 | sí |
| amb-04 | ambigua | 0.500 | sí |
| amb-05 | fuera_de_dominio | 0.379 | sí |
| man-11 | ambigua | 0.569 | NO |
| man-13 | fuera_de_dominio | 0.683 | NO |
| man-14 | fuera_de_dominio | 0.477 | sí |

5/7 contra 6/10 del baseline anterior. **La mejora es real y viene de POL-11:** `ec-01`/`ec-03` eran dos de los cuatro fallos del 21-ago y ya no están acá — dejaron de ser "fuera de dominio" porque ahora la KB los responde. Quedan los dos fallos de siempre (`man-11`, `man-13`), donde el denso encuentra chunks "parecidos" y respondería con falsa confianza. Dato directo para la calibración del "no sé" en POL-9.

### 2.7 Casos `post_baseline` — sección APARTE, nunca promediados

68 queries agregadas después de que el baseline se midiera (55 de 11.3 + 13 de 11.5). **No se comparan contra ningún baseline** porque ninguno las midió, y la regla de no-regresión no les aplica (`eval.md` §2 y §6). Hasta 11.5 el runner directamente abortaba ante ellas; ahora tienen manejo real.

| Métrica | v1 sobre casos post_baseline |
|---|---|
| Recall@1 | 0.53 |
| Recall@5 | **0.99** |
| Precision@5 | 0.28 |
| MRR | 0.70 |

Recall@5 0.99 = **67 de 68**. La única falla es `pol11-fix-al004`, dejada fallando a propósito con su diagnóstico escrito (hallazgos 11.5): las dos mitades del artículo AL004 no son separables por vocabulario y el caso es una apuesta de POL-7, no un defecto de contenido.

### 2.8 Cobertura del índice (`kb_coverage_pct`) — tres lecturas

Agregar queries sube la cobertura casi por construcción, así que se reporta en tres lecturas sobre el mismo índice de 184 chunks:

| Lectura | n queries | `kb_coverage_pct` | huérfanos |
|---|---|---|---|
| A. orgánica sin las 13 queries nuevas de 11.5 | 96 | 91.8 % | 15 |
| B. orgánica + las 4 de artículos que no tenían ninguna query | 100 | 94.0 % | 11 |
| C. orgánica + las 13 | 109 | **98.4 %** | 3 |

El criterio de `kb-expansion.md` §7 (≥ 96 %) **se cumple solo en la lectura C**. Cuál de las tres es EL número del criterio es parte de lo que se pide firmar. `chunk_dominance_top1_ratio` máximo: **5.5 %** (umbral ADR-0005: 10 %).

---

## 3. Config exacta y reproducibilidad

- **Config:** v1 (dense-only) — embed Vertex + cosine exacto in-memory, sin BM25 ni RRF
- **KB:** 184 chunks (chunker discovery `source::heading`, saneado en 11.4) · hash índice `11eef1a591ae`
- **Corpus:** 115 queries (47 baseline + 68 post_baseline) · sha `e837fc29ad70` · `src/eval/corpus/corpus.jsonl`
- **Embeddings:** `text-embedding-005` (Vertex) · top-K = 5
- **Comando:** `uv run python -m src.eval.run --config v1 --fecha 2026-08-24`
- **Determinismo verificado:** el eval se corrió **dos veces**; reportes byte-idénticos (`diff` vacío). Los embeddings quedan congelados en `src/eval/cache/`.
- **Costo real del experimento (11.5):** **USD 0.0000091** — 14 embeddings nuevos (las 13 queries agregadas); todo lo demás salió de cache caliente y el segundo run costó **USD 0.00000**. Costo del corpus completo embebido si se partiera de cero: USD 0.00066.
- **Latencia:** percentiles del embed de query (Vertex, congelados en cache en su primer run); el cosine in-memory agrega < 1 ms (p95 medido: 0.1 ms) y no entra al reporte por determinismo.
- **Paridad JS/Python:** sigue **INAPLICABLE** y diferida a POL-7 (`eval.md` §4). El eval indexa 184 chunks `source::heading`; el Worker consulta 261 chunks `stem#i`. La brecha ya no es solo de intros: producción arrastra 2 chunks de puro footer y ~15 con el footer embebido (hallazgos 11.4 #3).

---

## 4. Referencia histórica — baseline v1 original, corrida del 2026-08-21

> **No se borra: es el registro de que el instrumento cambió y por qué.** Este es el baseline que publicó 10.4, midió el gate de v2 y desbloqueó POL-6/7/9/11 (PR #6). Sus números son válidos **para el índice de 52 chunks y la KB de 20 artículos**, que ya no existen — compararlos contra un run actual sin leer la sección 1 de este documento produce una conclusión falsa.

**Fecha:** 2026-08-21 · **Config:** v1 dense-only · **Corpus:** v1 (47 queries) · **KB:** 52 chunks · hash índice `a0cd72dab0ef` · corpus sha `e93d63672084`

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

Sobre 37 queries con chunk esperado; las 10 sin chunk esperado (fuera de dominio y ambiguas sin respuesta defendible) se evaluaban solo por answer_type.

**Por idioma:** en (n=17) 0.71 / 0.88 / 0.28 / 0.79 · es (n=20) 0.70 / 0.95 / 0.34 / 0.80 — sin sesgo severo (≤ 0.07).

**Por categoría:** ambigua (n=1) 1.00 / 1.00 / 0.60 / 1.00 · tipica (n=29) 0.79 / 0.97 / 0.33 / 0.87 · typo_jerga (n=7) 0.29 / 0.71 / 0.20 / 0.46.

**answer_type (umbral 0.50):** gatillaba en `amb-01` (0.383), `amb-03` (0.469), `amb-04` (0.455), `amb-05` (0.371), `ec-02` (0.415), `man-14` (0.477); **NO** gatillaba en `ec-01` (0.601), `ec-03` (0.676), `man-11` (0.553), `man-13` (0.690).

**Lectura original (dónde perdía v1):**

1. **typo/jerga era el punto débil claro** (Recall@1 0.29, MRR 0.46 vs 0.87 de las típicas). Las únicas 3 queries que ni siquiera llegaban al contexto eran de término exacto: `typo-03` (reautorizar oauth), `typo-04` (api key rotation) y `amb-02` (TikTok Ads). *Sigue vigente en 2026-08-24, con `typo-05` sumada.*
2. **El umbral 0.50 funcionaba para lo claramente ajeno, no para lo cercano al dominio:** fallaba en `ec-01`/`ec-03` (códigos de error) y en `man-11`/`man-13`. *Los dos casos de códigos los resolvió POL-11.*
3. **Fallas de Recall@1 con acierto en top-5** (8 casos): el chunk correcto llegaba al prompt pero no de primero — mejorable por re-ranking sin tocar la KB. *En 2026-08-24 este grupo creció; sigue siendo el diagnóstico de POL-7.*

**Reproducibilidad de aquella corrida:** comando `uv run python -m src.eval.run --config v1 --fecha 2026-08-21`; determinismo verificado (dos runs byte-idénticos); costo real USD 0.00015 (99 embeddings: 52 chunks + 47 queries).
