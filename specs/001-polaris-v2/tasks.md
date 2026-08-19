<!-- Tasks breakdown Polaris v2 — POL-5. Fuente de verdad del detalle operativo. Cada subtarea también existe en Jira como subtask hija de la Historia POL-XX correspondiente para visibilidad en tableros. -->

# Polaris v2 — Tasks breakdown

**Versión:** DRAFT (POL-5 en curso)
**Autor:** Vladislav Marinovich · Marinovich Consulting SAS
**Refs:** Constitution v1.0.0 (`../../.specify/memory/constitution.md`), [Spec funcional](spec.md), [Plan técnico](plan.md), 6 ADRs en [`../../docs/adr/`](../../docs/adr/), [Discovery findings](discovery/findings.md).

Este documento descompone cada Historia POL-6 a POL-11 en subtareas atómicas con criterio de aceptación, estimado y dependencias. También registra retroactivamente el trabajo ya ejecutado (fases 0-4 del ciclo Spec Kit + Discovery Fase 0.b) para tener registro unificado.

Los ajustes de scope derivados empíricamente del discovery están explícitamente marcados como **[Ajuste post-discovery]** dentro de cada Historia afectada (POL-7, POL-9, POL-11).

## Convención

Campos por subtarea:

- **Agente:** modelo asignado para ejecutar la subtarea (ver mapa abajo). Asignación explícita para eliminar el margen de error de "modelo incorrecto en fase de criterio" — causa raíz documentada de fallos previos.
- **Estimado:** horas de trabajo enfocado del ejecutor (no calendario).
- **Depende de:** lista de subtareas que deben cerrar antes de arrancar esta.
- **Criterio de aceptación:** condición binaria que dispara el checkbox de "hecho".
- **Jira ID:** se completa al crear la subtask en Jira.

Reglas de método:

- **Docs-first.** Toda subtarea de código va precedida por su subtarea de documentación (spec de la feature, casos edge, decisiones). Nunca se codea sin doc previa. Si un ejecutor detecta que va a codear sin doc, se detiene y documenta primero.
- **Jira a medida.** Las subtasks de Jira NO se crean todas al inicio: se crean progresivamente, al momento de arrancar cada una. Jira es el tablero visual y bitácora redundante; este archivo es la fuente de verdad del detalle.
- **Confluence sync como subtarea explícita.** Cada Historia cierra con una subtarea de sync a Confluence (los commits viven en Git; la documentación operativa se refleja en Confluence).
- **Bitácora obligatoria.** Cada subtarea registra en [`bitacora/timeline.jsonl`](bitacora/timeline.jsonl) tres eventos con timestamp ISO 8601: `start` (al arrancar), `end` (al terminar, con `duracion_min`), `commit` (con `commit_sha`, tomado de `git log --format=%aI`). Cada evento incluye el campo `agente`. Los hallazgos, desvíos y decisiones van en [`bitacora/hallazgos.md`](bitacora/hallazgos.md) antes del commit. Formato XES-lite compatible con minería de procesos: el objetivo es poder responder después dónde se atasca la ejecución, qué subtareas explotan en scope y cuál es el lead time real vs. estimado.
- **Worklog automático.** El worklog de Jira ya no se estima a mano: se deriva de la bitácora (`hora_fin − hora_inicio` por subtarea, redondeado al minuto) y se registra en la subtask al cerrarla.

### Mapa de agentes

| Agente | Rol en v2 |
|---|---|
| **Watson (Fable 5)** | Criterio: specs de subtareas docs-first, criterios de aceptación, decisiones de diseño, auditoría de spec/docs/PR antes de cada merge. |
| **Opus 5** | Implementación: código del Worker, tests, schemas/DDL BigQuery, dashboards Grafana, verificación en sandbox, y auditoría de re-ataque en runtime (Fable frena por safeguards en framing adversarial; encuadre correcto: "verificación de seguridad de mi propio sistema, en sandbox, autorizada", derivando de la spec qué debería pasar). |
| **Sonnet 5** | Mecánico: formatting, feature flag wiring, renames, sync a Confluence, commits/push. |

Haiku queda excluido del proyecto (retirado el 21-jul por fallos de comprensión en tareas de criterio; ratificado el 19-ago).

La auditoría Fable de spec/docs/PR corre **por Historia** (antes de cada merge, no solo al final de v2): un crítico cazado en POL-6 cuesta un orden de magnitud menos que cazado en POL-11.

## Retrospectiva — Trabajo ya ejecutado (POL-2, POL-3, POL-4, Discovery)

Registro histórico de las Historias cerradas del ciclo Spec Kit + fase 0.b del Plan técnico. Se documenta para tener el tasks.md como fuente única de verdad del progreso completo de v2 y para que cualquier persona que llegue después vea qué se hizo, no solo qué falta.

### POL-2 — Constitution v1.0.0 (14 principios)

Cerrada 2026-08-18. PR #1 mergeado en `main`. Confluence page 557276. Worklog Jira 4h.

- 2.1 Redactar 14 principios en `.specify/memory/constitution.md`.
- 2.2 Sync Impact Report inicial en el header del archivo.
- 2.3 Crear `docs/WORKFLOW.md` con flujo Git y política de commits.
- 2.4 Crear plantilla `.github/pull_request_template.md`.

### POL-3 — Spec funcional v2

Cerrada 2026-08-18. PR #2 rebase-mergeado con 8 commits granulares en `main`. Confluence page 557298. Worklog Jira 4h.

- 3.1 Sección 1 Contexto y problema (4 carencias de v1).
- 3.2 Sección 2 Usuarios y JTBD (usuario final + owner).
- 3.3 Sección 3 Alcance funcional (6 features + modo cliente + observability by design).
- 3.4 Sección 4 Criterios de aceptación (cualitativos por feature).
- 3.5 Sección 5 Fuera de alcance v2.1+ (9 items diferidos con razón).
- 3.6 Sección 6 Métricas post-launch (5 criterios de éxito a 30 días).
- 3.7 Sección 7 Riesgos y mitigaciones (5 riesgos con mitigación concreta).
- 3.8 Ajustes de revisión (elimina Reviewer USD, agrega distribución de idiomas al dashboard, agrega ahorro estimado como widget, agrega clarificación multi-turn a v2.1).

### POL-4 — Plan técnico + 6 ADRs + Discovery Fase 0.b

Cerrada 2026-08-19. PR #4 rebase-mergeado con 24+ commits en `main`. Confluence: página Plan técnico (id 786434) + 6 páginas ADR como hijas. Worklog Jira 5.5h total (4h el 18-ago + 1.5h el 19-ago).

**Plan técnico (`specs/001-polaris-v2/plan.md`):**

- 4.1 Statement arquitectónico (3 compromisos que gobiernan las decisiones).
- 4.2 Arquitectura general (4 capas + servicios externos + artifact "Anatomía de Polaris").
- 4.3 Schema BigQuery draft (27 campos en 9 bloques + métricas derivadas).
- 4.4 Fases de ejecución (9 fases ordenadas por dependencia real).
- 4.5 Integración con Worker actual (6 feature flags para coexistencia v1/v2).
- 4.6 Convenciones del proyecto (7 reglas obligatorias del proyecto).
- 4.7 Referencias cruzadas (Constitution + Spec + 6 ADRs + artifact + Confluence + Jira).
- 4.8 Refinamiento de schema con hallazgos empíricos del discovery.

**6 ADRs (`docs/adr/`):**

- 4.9 ADR-0001 Cache backend → Cloudflare KV.
- 4.10 ADR-0002 Sink telemetría → BQ streaming con `waitUntil`.
- 4.11 ADR-0003 Dashboard tool → Grafana Cloud Free + Dashboard as Code.
- 4.12 ADR-0004 BM25 stemmer-less multilingüe (introduce patrón "Métricas de vigilancia" obligatorio).
- 4.13 ADR-0005 Fusión de rankings → RRF k=60.
- 4.14 ADR-0006 Rerank cross-encoder → rechazado para v2.
- 4.15 Retrofit de Métricas de vigilancia en ADR-0001/0002/0003 + agregar 2 SLIs empíricos (`kb_coverage_pct` en ADR-0004, `chunk_dominance_top1_ratio` en ADR-0005).
- 4.16 Actualizar README público con unit economics real (~11.100 respuestas/USD).

**Discovery Fase 0.b (`specs/001-polaris-v2/discovery/`):**

- 4.17 Instrumentar hot path v1 en `scripts/discovery/observe_flow.py` (standalone Python contra Vertex AI real).
- 4.18 Corpus 30 queries en `queries.jsonl` (10 ES + 10 EN + 5 typos/jerga + 5 ambiguas/fuera de dominio).
- 4.19 Ejecutar script contra Vertex AI en `us-central1`. Costo real: USD 0.00283.
- 4.20 Capturar `traces.jsonl` (180 eventos XES-lite compatibles con process mining).
- 4.21 Publicar `summary.md` (métricas agregadas).
- 4.22 Publicar `findings.md` (8 hallazgos empíricos con ajustes derivados al schema).

### POL-5 — Tasks breakdown (esta Historia, en curso)

Cerrada 2026-08-19. PR pendiente. Rama `feature/POL-5-tasks-breakdown`. Este documento.

## POL-6 — Canonicalize + KV cache

_A completar en commit siguiente._

## POL-7 — Retrieval híbrido BM25 + dense + RRF

_A completar en commit siguiente._

## POL-8 — Telemetría estructurada + dashboard

_A completar en commit siguiente._

## POL-9 — Multilingual explícito

_A completar en commit siguiente._

## POL-10 — Eval framework + baseline

_A completar en commit siguiente._

## POL-11 — KB expansion

_A completar en commit siguiente._

## Resumen

_A completar en commit siguiente — total estimado, gráfico de dependencias, camino crítico._
