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

## [2026-08-21] POL-10 (10.5) — Auditoría Fable del trabajo del ejecutor

**Veredicto: CERO CRÍTICOS. Aprobado para merge.**

**Verificado de forma independiente (no confiando en el reporte del ejecutor):**
- Las 4 fórmulas de métricas revisadas a mano contra eval.md §3 — correctas, incluida la exclusión de queries sin chunk esperado y el argsort estable ante empates.
- Determinismo reproducido por el auditor: dos runs propios → reportes byte-idénticos, gasto incremental $0.00000 (99 cache hits).
- La tabla global publicada en `baseline.md` coincide valor por valor con el run de auditoría (Recall@1 0.70, Recall@5 0.92, P@5 0.31, MRR 0.80, p50 176, p95 498, answer_type 6/10).
- Corpus: 47 queries válidas (validador ✔), composición razonable (29 típicas / 7 typo_jerga / 7 fuera_de_dominio / 4 ambiguas · 26 ES / 21 EN), spot-check de etiquetas (es-06, amb-02, en-03) defendibles. Tests 9/9 ✔. Cache gitignoreado ✔.
- Los 4 bloques de hallazgos del ejecutor son honestos y valiosos (divergencia de chunkers, re-etiqueta amb-02, secciones comidas por el filtro "still stuck?", estampa fable5 honesta).

**Menores registrados (deuda, no bloquean):**
1. **`post_baseline` es guard fail-fast, no la sección aparte que pide el spec §2/§6.** Correcto hoy (no existen casos); DEBE implementarse antes de que 9.8 agregue casos — es prerequisito de 10.7.
2. **Heurística de costo (chars/4) duplicada** en `run.py` y `embed_cache.py` — unificar en un solo lugar cuando se toque el módulo (riesgo de divergencia silenciosa).
3. **Enmienda de contrato aplicada por el auditor:** eval.md §4 ahora refleja que la paridad JS/Python queda diferida a POL-7 (chunkers divergentes 52 vs 90) — el spec no puede prometer lo que la realidad no permite.

**Directiva nueva de Vlad (21-ago, durante la auditoría):** Polaris tiene routing a staff para preguntas que el bot no debe resolver (el schema ya lo contempla: `route: escalate_human`). El corpus de eval NO tiene esa categoría hoy. Directiva: cuando el corpus crezca (9.8 / 10.7), agregar categoría `staff_only` con `expected_route: escalate_human` (ej. disputas de facturación, borrado de cuenta) — el "no sé" y el "esto lo ve un humano" son resultados distintos y se miden distinto.

## [2026-08-21] POL-11 (11.1) — Auditoría de huérfanos: el 25% invisible era el instrumento

**Contexto:** auditoría previa a la expansión de KB, con el eval de POL-10 como instrumento (config v1, cache caliente, USD 0). Producto: `specs/001-polaris-v2/kb-audit.md`. Módulo reproducible nuevo: `src/eval/coverage.py`.

**1. El bloqueo blando del discovery se levanta: los 13 huérfanos eran artefacto de medición.** Replicando la medición exacta del discovery (30 queries, top-3) el eval devuelve **75.0% de cobertura y los mismos 13 chunks** — el instrumento está validado. Con el corpus de 47 queries y top-5 la cobertura es 98.1% (1 huérfano). **La cifra que se debe citar es 96.2% (2 huérfanos)**, excluyendo las 6 queries que yo mismo escribí en 10.2 apuntando a huérfanos (`man-02`..`man-05`, `man-09`, `amb-02`): usar cobertura autogenerada como prueba de salud de la KB sería circular. Decisiones: 8 aceptar y vigilar (sesgo de corpus), 4 reescribir (texto genérico / brecha de vocabulario), 1 cubrir con query nueva.

**2. CORRIJO UN HALLAZGO MÍO (10.2, #3): la pérdida por el filtro "still stuck?" NO es pérdida de KB.** Escribí que el filtro "se come la última sección real de varios artículos" y lo llamé "pérdida real de KB que POL-11 debe corregir". Es falso en su parte importante: el chunker de **producción** (`src/chunk_kb.py`) strippea el footer del texto crudo ANTES de segmentar y captura las 70 secciones + 20 intros = **90 chunks, cero pérdida**. El que pierde es el índice del **eval/discovery** (52 chunks): descarta 18 secciones completas —todas con contenido real, 97-436 chars, incluidos los dos bloques de Troubleshooting de conectores y `users-permission-denied::Role reference`— y además **indexa 2 chunks de puro boilerplate** (`reports-not-arriving::still-stuck?`, `connectors-reauthorize-expired::still-stuck?`).

**3. Ese índice degradado daña el baseline de forma medible y trazable.** Los 2 chunks-basura aparecen 11 veces en top-5: **11 de 47 queries (23%) reciben un chunk que solo dice "contact support"** (4.7% de los slots de contexto). Dos consecuencias con cadena causal completa: (a) en `man-13` el top-1 ES un footer con score 0.690 → el umbral 0.50 no gatilla y explica uno de los 4 fallos de answer_type del baseline; (b) en `es-09` y `typo-04` el footer ocupa un puesto del top-5 mientras `connectors-reauthorize-expired::how-to-reconnect` —el chunk esperado de 4 queries y de 2 de las 3 fallas de Recall@5— queda en rank 4 o fuera: **el footer le roba el contexto a su propio artículo**. Sanear el índice NO se hizo acá (scope freeze de 11.1 + cambiaría el índice bajo un baseline recién publicado); propuesta en kb-audit.md §3: hacerlo en **11.4**, y aceptar explícitamente que exige re-correr el baseline y re-etiquetar las queries afectadas. Es también el prerrequisito de la paridad JS/Python diferida a POL-7.

**4. DESVÍO del encargo: las cifras rancias se corrigieron 89→90, NO 89→52.** El criterio de 11.1 (y el hallazgo #4 de POL-5) pedían "corregir 89→52". Verificado en los 4 documentos: las cuatro menciones describen el índice de **producción** (Mongo `polaris.kb_chunks`, vectores bundled del Worker, `src/vectorstore.py`), que hoy tiene **90** chunks — evidencia: commit `c78eeb8` "Re-exportar vectores KB (90 chunks)" y el conteo actual de `src/chunk_kb.py`. Escribir 52 ahí habría reemplazado una cifra vieja por una **falsa**, atribuyendo al índice de producción el conteo del índice del eval. Se corrigió a 90 en `spec.md:13` (precisando "intro + secciones H2"), `docs/adr/0001` (2 lugares), `docs/BITACORA.md` (8 lugares; el sha `8e89b49` no se tocó) y `docs/mapa-matematicas-polaris.md` (1 lugar — **gitignoreado, corregido en disco pero NO versionado**). La distinción de índices queda documentada en kb-audit.md §3 y §5 para que la próxima lectura no vuelva a confundir 52 con 90.

**5. El chunk imán no se arregló, se diluyó.** `dashboards-not-loading::1.-check-your-internet-connection` sigue siendo top-1 en las mismas 4 queries genéricas; el ratio baja de 13.3% a 8.5% solo porque el denominador pasó de 30 a 47 queries. Queda bajo el umbral de 10% de ADR-0005 sin que nada mejorara. Recomendación: vigilar el conteo absoluto además del ratio, y mantener el re-chunkeo de ese artículo en 11.3.

## [2026-08-21] POL-11 (11.1) — Revisión Watson del kb-audit: aprobado con una precisión

**Verificado independientemente (medición propia, no la prosa del ejecutor):** producción 90 = 70 H2 + 20 intros exacto · eval 52 = 70 − 18 filtradas · los 2 chunks-basura existen y su mecanismo es fino (el filtro mira el CUERPO; en esos 2 artículos el footer vive bajo su propio heading `## Still stuck?` y por eso sobrevivió) · réplica del discovery al decimal (75.0%, mismos 13) · orgánico 96.2% · imán diluido a 8.5% · `man-13` footer top-1 con 0.690 ✓ · `typo-04` footer rank 5 (0.632) desplaza al esperado rank 6 (0.631) ✓ · cifras 89→90 correctas en los 3 archivos versionados.

**Una sobreafirmación corregida en el doc:** la tabla §2 implicaba que el footer explica ambas fallas de Recall@5; medido, `typo-03` no tiene footer en su top-5 — es gap puro de jerga (caso BM25/POL-7, no saneamiento). El resumen de chat del ejecutor arrastró la misma imprecisión. Corregido en kb-audit.md con los scores como evidencia. (El §3 del propio doc ya lo decía bien: `es-09` y `typo-04`.)

**Decisión de método (Vlad, 21-ago):** las auditorías formales por Historia (6.9, 7.8, 8.11, 9.10, 10.10, 11.6) pasan a un **chat auditor independiente** (tercer rol). Watson escribió los specs — auditarse a sí mismo compromete la independencia. Esta revisión de 11.1 queda como revisión del orquestador; la auditoría formal del PR de POL-11 (11.6) la hará el auditor externo.

**Pendiente de decisión de Vlad (propuesta del ejecutor, avalada por Watson):** sanear el índice del eval en 11.4 (strippear footer antes de segmentar, como producción) → exige re-correr baseline + re-etiquetar 4-6 queries. Sin eso, los deltas de v2 comparan contra un índice defectuoso.

## [2026-08-21] POL-11 (11.3) — Redacción de 55 artículos: la regla 12 cazó 8 problemas

**Contexto:** 40 artículos de códigos (ER 10 · PF 6 · PL 5 · RP 6 · AL 4 · DB 5 · AG 4) + 15 de módulos, KB de 20 → 75 artículos. 55 queries nuevas al corpus (`post_baseline:true`, `source:"pol11"`) + re-etiquetado de `ec-01/02/03`. Verificación de la regla 12 sobre las 58 queries nuevas y re-etiquetadas: **58/58 pasan** tras las correcciones de abajo. Costo de los embeddings exploratorios: ~USD 0.001.

**1. TRAMPA EVITADA: el cierre de soporte habitual habría dejado huérfano el último chunk de los 55 artículos.** El chunker del eval descarta cualquier sección cuyo cuerpo **contenga la frase** "still stuck?" — no solo la que la use como heading. Si hubiera cerrado los artículos con el "Still stuck? Contact support" de los 20 existentes, la última sección H2 de cada artículo nuevo (los bloques "How to fix…", justamente los que resuelven) habría desaparecido del índice: 55 chunks perdidos de entrada. Se usó un cierre sin esa frase ("If ER005 persists after reconnecting, contact support with…") y los 110 chunks nuevos sobreviven. **La regla 9 del checklist está mal formulada**: prohíbe el heading `## Still stuck?` cuando lo que hay que prohibir es la frase en cualquier posición. Propuesta para 11.4/11.5: corregir la redacción de la regla 9 en kb-audit.md §4 (y el saneamiento del índice elimina la causa de raíz).

**2. Cinco artículos nacieron huérfanos por brecha de vocabulario y se reescribieron (regla 12).** El fallo no estaba en la estructura sino en las palabras: el artículo describía el estado del sistema y el usuario describe su síntoma. Casos y arreglo (todos en el cuerpo, sin tocar headings, para no invalidar los chunk_ids ya etiquetados):
- `pl001` (rank 36 → 1): faltaba el caso concreto "agregar una segunda cuenta de Google Ads"; el artículo solo hablaba de "connection limit".
- `db003` (rank 12 → 1): faltaba "los números se ven viejos / de hace dos días"; decía solo "freshness delayed".
- `db005` (rank 12 → 1): faltaba que un widget **es** una card, y que el síntoma es que **Add Card** deja de funcionar. Vocabulario que la propia KB vieja usa ("+ Add Card").
- `al004` (rank 17 → top-5): faltaba "Polaris apagó mi alerta solo / la deshabilitó automáticamente".
- `pl003` (rank 6 → top-5): faltaba la pregunta real del usuario, "¿deja de funcionar Polaris si rechazan la tarjeta?".

**3. `roles-what-each-role-can-do` se reenfocó dos veces: su tema ya estaba cubierto.** Falló la regla 12 con "what can a viewer do" (rank 7) porque `pf006`, `users-invite-roles::understanding-roles` y `users-permission-denied` ya responden eso — y lo responden bien. Reescribirlo para ganarle a chunks correctos habría sido empeorar la KB. Se reenfocó a lo que ningún artículo hacía: **comparar los tres roles y mapear cada rol al código de error que produce** (PF002/PF005/PF006 → qué rol pedir). Con su query propia ("diferencia entre admin analyst y viewer") queda rank 1. Lección para 11.2: el plan pedía 2 artículos de "permisos por rol y seguridad", pero el hueco real era solo seguridad; el de roles se justifica por su ángulo, no por el tema.

**4. Tres fallas de la regla 12 eran MI etiquetado, no los artículos.** El generador de queries elegía el chunk por patrón de heading (`modo="fix"` → "how-to…"), y (a) los artículos de conector usan "Connecting the X account", así que el fallback etiquetó el chunk de datos aunque el artículo ganaba en rank 1-2; (b) para queries de diagnóstico ("¿por qué no me deja?") el chunk correcto es el que explica el límite, no el procedimiento. Corregido a etiqueta de artículo completo en `pol11-conn-gads`, `pol11-conn-meta`, `pol11-pl001`, `pol11-db005`. **Aviso para el auditor:** una falla de la regla 12 puede ser un defecto de la etiqueta y no del artículo; verificar cuál antes de mandar a reescribir.

**5. Dos queries tienen más de un artículo correcto y la etiqueta lo reconoce.** `pol11-pf003b` ("hubspot appears blocked and asks me to upgrade") la responden igual de bien PF003 y PL002; `pol11-pf005` ("veo que el conector expiró pero no me deja reconectarlo") la responden PF005 y el artículo viejo `connectors-reauthorize-expired`. El corpus admite varios chunks válidos (eval.md §2), así que se etiquetaron ambos en vez de forzar un ganador artificial. No es laxitud: forzar un único dueño habría medido preferencia de redacción, no calidad de retrieval.

**6. Deuda respetada, no tocada: el guard `post_baseline` del runner.** `cargar_corpus()` aborta con las 55 queries nuevas (`post_baseline:true`), tal como está declarado en kb-expansion.md §5 y en la auditoría 10.5. La verificación de la regla 12 se hizo con un script exploratorio que lee el JSONL directo, sin modificar el runner. **Sigue siendo prerrequisito de 11.5**, y ahora es bloqueante de hecho: el eval no corre de punta a punta hasta que la sección aparte de `post_baseline` esté implementada.

**7. Sin números de límites inventados.** El producto define los planes por "número de conexiones" pero deja el número sin definir (`polaris-producto.md`: "pocas (definir nº en 11.2)"), y 11.2 no lo fijó. Los artículos de PL001/PL005/PF004 siguen el estilo de la KB vigente —`billing-plans.md` dice "up to a limited number of connectors" sin cifras— y remiten a **Settings > Billing** para el valor real. Inventar cifras habría creado producto durante la redacción, que es exactamente lo que el §8 de kb-expansion prohíbe.
