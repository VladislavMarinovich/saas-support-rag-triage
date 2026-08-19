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
