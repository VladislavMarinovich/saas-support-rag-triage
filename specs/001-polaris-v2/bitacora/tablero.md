# Tablero de orquestación — Polaris v2

> ✍️ **Escriben: el ORQUESTADOR (Watson) y los EJECUTORES.** El AUDITOR **no edita este archivo** — su registro es [`registro-auditoria.md`](registro-auditoria.md). Un escritor por archivo (Constitución v1.1.0).

Hilo de orquestación entre sesiones. **Cualquier sesión nueva lee este archivo primero** y continúa desde acá. Vive en el repo, no en la memoria de un agente — el 24-ago el handoff en memoria falló y esa es la razón de que este archivo exista (ADR-0007).

No reemplaza a [`tasks.md`](../tasks.md) (tareas y criterios), Jira (bloques y worklog) ni la rama git (código). Captura el **hilo**: qué pasó, veredicto, qué sigue, qué espera firma.

---

## 📍 ESTADO VIVO — punto de rehidratación

> **Actualizar tras cada despacho y cada gate. Un vistazo = resumen completo.** Última actualización: **2026-08-24** (Watson) — POL-18 mergeado; 11.4.b cerrada y rama rebasada sobre main; sigue 11.5 (frontera).

- **Modo:** Watson orquesta tripulación efímera; ejecutores implementan por bloque; auditor renovado en sesión aparte. **Gate con firma de Vlad en las 3 fronteras** (re-estampar baseline · `LIVE=true` desplegado · merge a `main`).
- **Rama viva:** `feature/POL-11-kb-expansion` (POL-11 al 60%) · rama de gobernanza: `docs/POL-18-gobernanza-orquestacion`.
- **El gate de v2 está ABIERTO:** baseline v1 publicado y mergeado (PR #6). POL-6/7/9/11 desbloqueadas.

### Cola inmediata

| # | Bloque | Estado | Quién |
|---|---|---|---|
| 1 | ~~POL-18 gobernanza~~ | ✅ **mergeado** (PR #7, firma de Vlad 24-ago) — reglas vigentes | Watson |
| 2 | ~~11.4.b~~ `LIVE` a variable de entorno | ✅ **hecha y verificada** (ver entrada abajo) | ejecutor Opus |
| 3 | **11.5** etiquetas + queries de arreglo + **re-estampar baseline** | ⏳ prompt entregado, sin despachar — **FRONTERA: firma de Vlad** | ejecutor Opus |
| 4 | **11.6** auditoría adversarial del PR completo de POL-11 | ⧗ pendiente | **auditor en chat aparte** |
| 5 | POL-9 → POL-6 → POL-7 → POL-8 → POL-10.B | ⧗ pendiente | según `tasks.md` |

### Esperando firma o decisión de Vlad

- **Re-estampar el baseline en 11.5** (frontera: instrumento de medición). Vlad dio GO al saneamiento el 21-ago; la firma del re-estampado se pide al ver los números nuevos.
- **Deuda declarada con dueño:** mecanizar el Tier 1 como hook pre-commit (hoy es métrico vía eval). Se evalúa al cerrar POL-11 (ADR-0007, alternativa diferida).

### Historias cerradas

| Historia | Estado | Evidencia |
|---|---|---|
| POL-2 Constitution · POL-3 Spec · POL-4 Plan + 6 ADRs + discovery | ✅ Listo | PRs #1, #2, #4 · Confluence 557276 / 557298 / 786434 |
| POL-5 Tasks breakdown | ✅ Listo | PR #5 · Confluence 1245185 · 60 subtareas / ~57.75h |
| POL-10.A Eval framework + baseline (**el gate**) | ✅ mergeado, POL-10 En curso (falta 10.B) | PR #6 · Confluence 1277954 / 1310721 · R@1 0.70 · R@5 0.92 · MRR 0.80 |
| POL-11 · 11.1 auditoría de huérfanos | ✅ Listo | `kb-audit.md` — el "25% invisible" era artefacto del instrumento |
| POL-11 · 11.2 spec de expansión | ✅ Listo | `docs/features/kb-expansion.md` — 75 artículos objetivo |
| POL-18 Gobernanza · Constitución v1.1.0 | ✅ Listo | PR #7 · ADR-0007 · squash mecanizado en el repo |
| POL-11 · 11.3 redacción + 11.4 saneamiento | ✅ hechas, revisadas por Watson | 55 artículos · índice 52→184 sin perder ids · producción 90→261 chunks |

### Deuda abierta que bloquea 11.5

1. **No-regresión falla:** Recall@5 0.92 → 0.86 en las 37 queries del baseline. Causa: etiquetas del corpus sin revisar tras expandir la KB (`eval.md` §2 lo exigía). **Guardarraíl:** revisar etiquetas no es ajustarlas hasta que suban los números; cada cambio se justifica por escrito y los 3 casos de término exacto (`typo-03`, `typo-04`, `amb-02`) **se dejan fallando** — son la apuesta que POL-7 debe ganar.
2. **Cobertura orgánica 94.0%** vs 96% que exige `kb-expansion.md` §7. 6 de los 10 huérfanos son la mitad **accionable** de artículos nuevos (el "cómo se arregla" no se recupera, el "qué significa" sí).
3. **Guard `post_baseline` bloqueante de hecho:** el runner aborta con las 55 queries nuevas. Prerrequisito duro de 11.5.

### Registro de orquestación

- **Costo de experimentos hasta hoy:** discovery USD 0.00283 · baseline 10.4 USD 0.00015 · exploratorios 11.3 ~USD 0.001 · re-embed 11.4 (pendiente de reportar). Los runs de eval con cache caliente cuestan USD 0.
- **Unit economics del producto:** ~11.100 respuestas por USD 1 (`gemini-2.5-flash-lite`).

---

## Bitácora por bloque

*Entradas en orden cronológico inverso (lo más reciente arriba). Cada bloque cierra con: qué hizo el ejecutor · veredicto de la revisión · qué sigue.*

### [2026-08-24] POL-18 — Gobernanza: Constitución v1.1.0

**Qué se hizo (Watson).** ADR-0007 + enmienda de la Constitución a v1.1.0 (orquestación de agentes, gate en 3 fronteras declaradas, defensa de drift en 2 cadencias, un escritor por archivo, este tablero). Corrige además una contradicción rezagada: la cadena de trazabilidad decía "squash-merge" cuando la política es rebase desde el 18-ago.

**Motivación empírica, no teórica.** Dos hechos: el handoff en memoria falló al retomar el 24-ago; y la ausencia de gate de radio de impacto costó Recall@5 0.92→0.86 en POL-11 pese a que `eval.md` §2 ya lo exigía por escrito.

**Aporte de vuelta al método (MC SFE).** Polaris instancia el Tier 1 de forma **métrica** (no-regresión numérica) frente al Tier 1 **estructural** de Consola SOS (estampas de versión, cobertura enum→emisor). Segunda instanciación del mismo pilar con mecanismo distinto — evidencia de que la cadencia generaliza y su implementación depende del dominio.

**Qué sigue.** Revisión del diff por Vlad → merge (frontera) → despachar 11.4.b.

### [2026-08-24] POL-11 · 11.4.b — `LIVE` como variable de entorno

**Despacho.** Agente efímero (ejecutor Opus 5) lanzado por Watson desde el chat. Duración 12m 56s · 60 tool calls · **145.510 tokens** de la sesión del agente.

**Qué hizo.** `LIVE` sale de `env.LIVE` vía `isLive()` con lista blanca de un solo valor: solo la cadena `"true"` enciende; ausencia, `"false"`, `"1"` o basura caen en `false` (resuelve la trampa de que en JS `"false"` es truthy). `vars.LIVE="false"` declarado en prod **y** en `env.dev`. Plantillas `.dev.vars.v1/.v2.example` versionadas, reales al `.gitignore`. `WORKFLOW.md` §10 documenta el flujo dev-antes-de-prod y la regla de firma. 6 commits, HEAD del bloque `9cd26a1` (pre-rebase).

**Verificación — PASÓ, con evidencia.** `wrangler dev` local con `LIVE=true`: `/api/triage` → **HTTP 200** citando `ER005 — Not synced with Google Ads` (primera vez que el índice de 261 chunks se ejercita por HTTP end-to-end, y valida de paso un artículo escrito en 11.3). Mismo binario sin `.dev.vars` → **503 demo_paused**, contrato idéntico. Prod y el dev público siguen en 503, **cero deploys** (dev sigue en `da8ac79a` del 21-ago). **Costo Vertex: USD 0,000211.**

**Revisión de Watson (primera pasada).** Verificado de forma independiente: la SA key **nunca entró a git** (`git log --all --diff-filter=A` sobre `.dev.vars*` solo devuelve los `.example`; `.gitignore` cubre `.dev.vars.*` con excepción para `*.example`); `isLive()` implementa la lista blanca como se pidió y respeta booleanos reales por `--var`. El ejecutor **no cruzó ninguna frontera**: no desplegó, no mergeó, y reportó la SA key en claro en vez de callarla.

**Desvío resuelto por Watson.** El ejecutor no pudo escribir en `tablero.md` porque la rama estaba 8 commits detrás de `main` y el archivo nació en POL-18 — decisión correcta la suya de no rebasar por su cuenta (un escritor por rama). Watson rebasó `feature/POL-11-kb-expansion` sobre `main` resolviendo 9 conflictos de `timeline.jsonl` por unión ordenada por timestamp (el archivo es append-only: la resolución correcta es conservar ambos lados, nunca elegir uno). Resultado: 73 eventos, cero duplicados.

**Qué sigue.** 11.5 — etiquetas + queries de intención-de-arreglo + **re-estampar el baseline (FRONTERA: firma de Vlad)**.

### [2026-08-21] POL-11 · 11.4 — Saneamiento del índice + re-embed

**Ejecutor (Opus).** Saneó `src/eval/kb_index.py` adoptando el criterio de producción (strippear el footer antes de segmentar): índice 168 → 184 chunks. Re-embed de la KB completa: producción 90 → 261 chunks. Creó además un entorno dev en workers.dev con D1 propia y la route de producción vacía — **desvío justificado**: el paso de deploy no tenía dónde desplegar, y POL-6 (KV) y POL-8 (BQ) lo necesitan igual.

**Veredicto de la revisión (Watson).** Aprobado. Verificado midiendo: +18 secciones recuperadas, −2 chunks basura, **cero ids perdidos y cero etiquetas del corpus rotas** (la restricción crítica). Preguntó antes de activar `LIVE=true` en la URL pública en vez de hacerlo — comportamiento correcto: eso es frontera.

**Qué sigue.** 11.4.b (`LIVE` a variable de entorno para poder probar en dev antes de prod, decisión de Vlad del 21-ago).

### [2026-08-21] POL-11 · 11.3 — Redacción de 55 artículos

**Ejecutor (Opus).** 55 artículos nuevos (40 de códigos de error + 15 de módulos sin cobertura), 75 totales. 55 queries al corpus. Reescribió 5 artículos que nacían huérfanos por brecha de vocabulario. Detectó que el chunker descarta secciones que **contienen** la frase "still stuck?", no solo las que la usan como heading — con el cierre habitual de la KB habría perdido los 40 bloques "How to fix".

**Veredicto de la revisión (Watson).** Contenido aprobado, no se reescribe. Verificado: las 3 queries de códigos pasaron de "no sé" a MRR 1.00 (la prueba de que la expansión sirvió) · cero imanes nuevos (el histórico bajó de 8.5% a 3.9%) · ningún artículo nace huérfano. **Regla 9 del checklist reformulada** (prohibir la frase, no el heading) y verificada empíricamente. **Dos bloqueos encontrados que el ejecutor no reportó** — ver "Deuda abierta" arriba.

**Qué sigue.** 11.5 resuelve los dos bloqueos antes de re-estampar.
