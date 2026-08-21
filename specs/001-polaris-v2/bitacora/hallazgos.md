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
