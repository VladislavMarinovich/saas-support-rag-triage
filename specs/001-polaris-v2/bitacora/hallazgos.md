<!-- Registro de hallazgos de ejecución Polaris v2. Append-only: cada entrada documenta findings, desvíos y decisiones tomadas durante una subtarea o Historia. Complementa timeline.jsonl (eventos con timestamp para minería de procesos) con el contexto humano que un JSON no captura. -->

# Polaris v2 — Registro de hallazgos

**Formato de entrada:** `## [fecha] POL-X.Y — título corto`, seguido de: qué se encontró, qué se decidió, y si hubo desvío del plan (con causa). Cada entrada la escribe el agente ejecutor al cerrar la subtarea, antes del commit.

**Relación con `timeline.jsonl`:** el timeline captura *cuándo* (eventos start/end/commit con timestamp ISO 8601, formato XES-lite compatible con minería de procesos); este archivo captura *qué se aprendió*. Un evento sin hallazgos no requiere entrada aquí.

---

## [2026-08-19] POL-5 — Nace la bitácora (backfill de fases de planeación)

**Contexto:** la bitácora se creó a mitad de POL-5, por decisión de Vlad de poder medir también cuánto cuesta *crear una spec*, no solo codearla.

**Hallazgo:** las Historias POL-2/3/4 se ejecutaron sin registro de hora de inicio real. Los únicos anclajes confiables son los timestamps de git (primer y último commit) y los worklogs de Jira (estimados a mano al cierre). Por eso el backfill usa eventos `commit_first`/`commit_last`/`worklog_total` con `"source":"backfill"` en vez de fabricar eventos `start`/`end` que nunca se midieron.

**Limitación conocida del backfill:** el gap entre commits NO es tiempo de trabajo puro (POL-4 muestra commit_first 18:00 del 18-ago y commit_last 08:21 del 19-ago — incluye la noche). Para POL-2/3/4 la duración confiable es el worklog de Jira, no la resta de timestamps. Desde POL-5 en adelante los eventos `start`/`end` se registran en vivo y el worklog de Jira se **deriva** de ellos (regla nueva: ya no se estima a mano).

**Dato para la minería:** costo de la fase de planeación completa del Spec Kit hasta ahora — POL-2 (constitution): 4h · POL-3 (spec): 4h · POL-4 (plan + 6 ADRs + discovery): 5.5h · POL-5 (tasks): en curso. Total planeación ≥ 13.5h antes de la primera línea de código de v2.

## [2026-08-21] POL-5 — Cuatro hallazgos de consistencia al escribir POL-8..11

**Contexto:** al mapear los bloques restantes (POL-8 a POL-11) contra `plan.md` §4 y los ADRs, aparecieron cuatro inconsistencias entre artefactos ya mergeados. Ninguna es de POL-5, pero POL-5 es el documento que las cita — escribirlo sin resolverlas propagaba el error.

**1. `spec.md` dice Looker; ADR-0003 decidió Grafana.** El spec (POL-3, 18-ago) nombra Looker Studio en §3, §4 y §6. ADR-0003 (POL-4, un día después) rechazó Looker explícitamente ("no versionable como código") y eligió Grafana Cloud Free + Dashboard as Code. `constitution.md` línea 35 también dice "(Looker)". **Decisión (Vlad):** el ADR gana; POL-8 se escribe contra Grafana y la subtarea 8.1 reconcilia `spec.md` + `constitution.md` (bump PATCH con Sync Impact Report).

**2. Camino crítico invertido en el borrador.** `plan.md` §4 exige que la Fase 1 (baseline con eval framework, POL-10 parcial) cierre ANTES de las Fases 2-6 — "ninguna medición vale sin baseline" (Principio XII). Pero POL-6 y POL-7 se escribieron con `Depende de: —` en su primera subtarea: nada bloqueaba contra el baseline. **Decisión (Vlad):** POL-10 se parte en 10.A (framework + baseline v1, gate) y 10.B (comparación final v1 vs v2, Fase 8); se agrega la dependencia del gate a 6.1 y 7.1 en commit de corrección propio (historial honesto: se ve que el hallazgo llegó después).

**3. Fase 6 (modo cliente) sin Historia.** `spec.md` §3 dice "seis features" pero lista siete comportamientos: los seis con número POL más "Respuestas en modo cliente", sin Historia en Jira ni bloque en tasks.md. Trabajo real (prompt v2, few-shot, validación manual de 10 respuestas) sin dueño ni estimado. **Decisión (Vlad):** entra como sub-bloque marcado `[Fase 6 — modo cliente]` dentro de POL-9 — mismo artefacto (`worker/prompts/system_v2.md`), evita dos PRs pisando el mismo archivo.

**4. Cifras rancias post-discovery.** El discovery midió 52 chunks reales; siguen diciendo "89 chunks": `spec.md:13`, `docs/adr/0001-retrieval-without-a-dedicated-vector-db.md:9`, `docs/mapa-matematicas-polaris.md:24`, `docs/BITACORA.md:85`. **Decisión:** se corrigen dentro de la subtarea 11.1 (auditoría de chunks huérfanos — mismo momento en que las cifras de la KB se vuelven a tocar), no en POL-5.

**Nota de registro:** este segmento corre con agente `watson-opus5` (no Fable): la sesión arrancó en Opus 5 y así queda registrado en el timeline — no se estampa un modelo que no fue. El criterio de los cuatro hallazgos quedó validado por decisión explícita de Vlad en sesión.

## [2026-08-21] POL-10/POL-11 — Decisión: catálogo de códigos de error en la KB

**Propuesta de Vlad (sesión 10.1):** la KB expandida debe incluir artículos de **códigos de error exactos** del producto (ej. `ER005 — Not synced with Google Ads`), tipo catálogo de troubleshooting.

**Por qué entra sin romper scope freeze:** la selección de temas nuevos es la subtarea 11.2 (criterio ya aprobado); esto es una directiva de contenido, no scope nuevo.

**Valor doble:**
1. **POL-7:** los códigos exactos son el caso canónico donde BM25 supera al denso (un embedding representa mal el token `ER005`; el índice léxico lo clava). Es el delta más demostrable de la tabla v1 vs v2.
2. **POL-10/11:** el corpus de eval (10.2) incluye 2-3 queries con códigos de error, etiquetadas `fuera_de_dominio` contra la KB actual (los artículos no existen aún). Cuando POL-11 escriba el catálogo, esas queries se re-etiquetan y pasan a grounded — la expansión de KB queda medida con números, no con sensación.

**Acciones derivadas:** 10.2 agrega la categoría de queries con código de error · 11.2 incluye "catálogo de códigos de error" en los criterios de selección de temas.

## [2026-08-21] POL-10 (10.2) — Hallazgos del etiquetado del corpus

**Contexto:** construcción del corpus etiquetado (47 queries: 30 discovery + 17 manuales) contra la KB vigente de 52 chunks. Reglas y decisiones de etiquetado documentadas en `src/eval/corpus/README.md`.

**1. Dos esquemas de chunking conviven en el repo — la paridad JS/Python está rota HOY.** El corpus y el eval usan el chunker del discovery (`source::heading`, 52 chunks, solo H2, sin intros). Pero producción usa otro: `src/chunk_kb.py` produce ids `stem#i` CON intros, y `worker/kb_vectors.json` (lo que el Worker JS realmente consulta) tiene **90 chunks** con ese esquema. Consecuencia: los rankings de este eval NO son comparables 1:1 con el Worker vivo — la regla de paridad de eval.md §4 (5 queries doradas + `test_parity.py`) es inaplicable hasta unificar el chunker. No bloquea el baseline (v1 vs v2 se comparan dentro del MISMO eval), pero POL-7 debe unificar el esquema de chunking/ids antes del test espejo, y la unificación cambiará los números absolutos. Relacionado: hallazgo #4 de POL-5 (cifras rancias "89 chunks").

**2. `amb-02` ("does Polaris support TikTok Ads") re-etiquetada: la KB ya la responde.** El discovery la clasificó fuera de dominio, pero `connectors-roadmap::paid-add-on-connectors` (actualizado post-discovery) la responde directo. v1 denso NO lo recuperó en top-3 (término exacto "TikTok Ads" — chunk huérfano del hallazgo §2 del discovery). Queda etiquetada `tipica`/`grounded`: es un caso donde el baseline v1 probablemente falla y BM25 (POL-7) debería clavar — delta demostrable.

**3. El chunker del discovery descarta la última sección de varios artículos.** La regla "descartar secciones cuyo cuerpo contenga 'still stuck?'" se come la última sección real cuando el footer boilerplate quedó dentro de su cuerpo: `alerts-not-firing` §4 (alerta pausada), `billing-plans` "How to check or upgrade", `connectors-connect-hubspot` "Troubleshooting", entre otras, NO existen como chunks. Se etiquetó contra el índice tal cual es (52 chunks) — es el instrumento vigente — pero es pérdida real de KB que POL-11 debe corregir junto con el re-chunkeo. Nota menor: la lista de huérfanos de `discovery/findings.md` §2 tiene 2 ids transcritos con typo (`you-are-entitled` vs `you're-entitled`; `spam/promotions` vs `spam-/-promotions`); el inventario canónico es el que produce `src/eval/kb_index.py`.

**4. Estampa de agente: `ejecutor-fable5`, no `ejecutor-opus5`.** El encargo pedía estampar `"agente":"ejecutor-opus5"` (tasks.md asignaba 10.2-10.4 a Opus 5), pero esta sesión corre en Fable 5. Rige la regla de la bitácora del 21-ago ("no se estampa un modelo que no fue"): el timeline es instrumento de medición y falsear el modelo corrompe el dato. Todos los eventos de esta ventana van como `ejecutor-fable5`.

## [2026-08-21] POL-10 (10.3) — Hallazgos del framework

**1. BLOQUEO EXTERNO: ADC de Google expirado — 10.4 no puede correr.** `gcloud auth application-default print-access-token` exige reautenticación interactiva ("Reauthentication is needed") que solo Vlad puede completar: `gcloud auth application-default login`. El framework quedó verificado por dos vías que no necesitan red: tests de métricas con casos a mano (9 tests ✔) y smoke end-to-end del pipeline con embeddings falsos en cache aislado (dos runs byte-idénticos ✔). Lo ÚNICO pendiente es el run real contra Vertex — es decir, toda la subtarea 10.4 (baseline.md) queda bloqueada hasta la reautenticación. Costo esperado del primer run: ~USD 0.0006 (47 queries + 52 chunks, ~$0.00015 derivado de tokens según el propio reporte del smoke).

**2. `test_parity.py` (eval.md §4) diferido a POL-7 — imposible hoy.** La regla de paridad JS/Python exige que el scoring Python produzca el mismo ranking que el Worker; pero el Worker consulta `worker/kb_vectors.json` (90 chunks, ids `stem#i`) y el eval usa los 52 chunks `source::heading` del corpus (hallazgo #1 de 10.2). No hay paridad posible entre índices distintos. El criterio de aceptación de 10.3 en tasks.md no exige el test de paridad; eval.md ya lo ataba al "test espejo en el Worker cuando POL-7 implemente BM25/RRF". Queda explícito: POL-7 debe unificar el chunker ANTES de escribir `test_parity.py`, y las 5 queries doradas se eligen en ese momento.

**3. Decisión de instrumento: la latencia reportada es solo el embed de la query.** El reporte congela las latencias de embed en el cache (primer run = latencias reales de Vertex; runs siguientes las reusan) y deja el cosine in-memory (~1-3 ms, discovery §1) en consola. Alternativa descartada: medir latencia viva en cada run — rompía el criterio de determinismo de 10.4 ("dos runs = números idénticos") por ruido de milisegundos sin valor informativo. El costo del corpus se deriva de tokens (determinista); el gasto incremental real del run va a consola.

## [2026-08-21] POL-10 (10.4) — Hallazgos del baseline v1

**Contexto:** ADC reautenticado por Vlad; eval corrido dos veces (reportes byte-idénticos ✔); baseline publicado en `specs/001-polaris-v2/baseline.md`. Costo real: USD 0.00015.

**1. La apuesta de POL-7 queda cuantificada ANTES de implementarla.** Las únicas 3 queries que no llegan al contexto (Recall@5 = 0) son de término exacto (oauth, api key, TikTok Ads), y typo_jerga rinde Recall@1 0.29 vs 0.79 de las típicas. Si BM25+RRF no mueve ESTOS números, POL-7 no está funcionando — criterio de éxito concreto para la tabla v1 vs v2.

**2. El umbral 0.50 del discovery generaliza a medias.** Con 10 casos sin chunk esperado (vs 4 del discovery): gatilla bien en lo claramente ajeno (6/10), pero los códigos de error inexistentes en la KB (ec-01 0.601, ec-03 0.676) y preguntas de producto sin artículo (man-13 0.690) puntúan ALTO — el denso encuentra vecinos plausibles y respondería con falsa confianza. Implicación: el "no sé" honesto de POL-9 no puede colgarse solo del score; y POL-11 (artículos de códigos) convierte estos 4 fallos en grounded medibles.

**3. Fix menor de formato en el run:** `Costo/query` se imprimía con 6 decimales y $0.0000002 se redondeaba a $0.000000 (mentira visual). Corregido a 7 decimales antes de publicar el baseline.
