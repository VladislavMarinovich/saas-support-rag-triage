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

Normalización de la query a forma canónica idioma-agnóstica + cache persistente en Cloudflare KV (ADR-0001). Comportamiento observable: dos fraseos equivalentes reciben la misma respuesta y la segunda es sensiblemente más rápida, preservando el idioma del query original.

**Referencias:** Spec §3 (Canonicalización + cache), Plan §4 fase correspondiente, ADR-0001, criterio de aceptación Spec §4.

#### 6.1 Documentar spec de canonicalize

- **Agente:** Watson (Fable 5)
- **Estimado:** 30 min
- **Depende de:** 10.4 (baseline v1 publicado — gate de Plan §4 Fase 1: ninguna mejora se implementa sin baseline contra el cual medirla, Principio XII)
- **Criterio de aceptación:** `docs/features/canonicalize.md` define input/output, la regla de forma canónica (ignora orden de palabras, mayúsculas, puntuación y variantes triviales de fraseo), los casos edge (typos, jerga, acentos, queries fuera de dominio) y cómo se preserva el idioma original para servir desde cache.
- **Jira ID:** —

#### 6.2 Implementar canonicalize en Worker

- **Agente:** Opus 5
- **Estimado:** 2h
- **Depende de:** 6.1
- **Criterio de aceptación:** módulo de canonicalización con tests unitarios que cubren los casos del spec 6.1 (incluyendo los 5 typos/jerga del corpus discovery); gobernado por feature flag `V2_CANONICALIZE` (off = comportamiento v1 intacto).
- **Jira ID:** —

#### 6.3 Documentar spec del KV cache

- **Agente:** Watson (Fable 5)
- **Estimado:** 30 min
- **Depende de:** 6.1
- **Criterio de aceptación:** `docs/features/kv-cache.md` define el diseño de key (hash de forma canónica), el layout del value (respuesta + idioma + metadata mínima), TTL configurable, política de invalidación y qué NO se cachea (respuestas de confianza baja, `top1_score < 0.50` según hallazgo del discovery).
- **Jira ID:** —

#### 6.4 Crear namespace KV + wiring de configuración

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 6.3
- **Criterio de aceptación:** namespace KV creado, binding en `wrangler.toml`, TTL parametrizado por variable de entorno; deploy a entorno dev verificado sin afectar v1.
- **Jira ID:** —

#### 6.5 Implementar read/write path del cache

- **Agente:** Opus 5
- **Estimado:** 2h
- **Depende de:** 6.2, 6.4
- **Criterio de aceptación:** hot path consulta cache antes de retrieval; miss ejecuta cadena completa y persiste; hit sirve respetando idioma original; todo tras `V2_CANONICALIZE`. Un fallo de KV nunca rompe la respuesta al usuario (Principio III).
- **Jira ID:** —

#### 6.6 Tests de integración cache hit/miss + TTL

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 6.5
- **Criterio de aceptación:** suite cubre hit, miss, expiración por TTL, colisión de forma canónica entre idiomas distintos, y flag off = cero interacción con KV.
- **Jira ID:** —

#### 6.7 Auditoría de re-ataque en runtime (envenenamiento de cache)

- **Agente:** Opus 5 _(no Fable: framing adversarial dispara safeguards; encuadre "verificación de seguridad de mi propio sistema, en sandbox, autorizada")_
- **Estimado:** 1h
- **Depende de:** 6.6
- **Criterio de aceptación:** verificado que un usuario no puede envenenar el cache para otros (inyección vía query, colisiones de key forzadas, respuestas de baja confianza cacheadas); hallazgos y mitigaciones en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 6.8 Verificación en sandbox con corpus del discovery

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 6.6
- **Criterio de aceptación:** las 30 queries del corpus discovery corridas contra dev: fraseos equivalentes producen cache hit, latencia de hit sensiblemente menor a p50 del path completo (baseline medido: ver README), idioma preservado en el 100% de los hits.
- **Jira ID:** —

#### 6.9 Auditoría Fable del PR

- **Agente:** Fable 5 (auditor externo)
- **Estimado:** 45 min
- **Depende de:** 6.7, 6.8
- **Criterio de aceptación:** diff completo del PR auditado contra spec 6.1/6.3 y Constitution; cero críticos abiertos; hallazgos registrados en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 6.10 Sync a Confluence + cierre

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 6.9
- **Criterio de aceptación:** docs de features reflejados en Confluence bajo el árbol del Plan técnico; worklog derivado de bitácora registrado en Jira; Historia POL-6 transicionada a Listo.
- **Jira ID:** —

**Total estimado POL-6: ~9.75h** (10 subtareas; el par docs-first + auditorías suma ~3.25h sobre las ~6.5h de implementación pura — ese es el costo del método y se mide en la bitácora).

## POL-7 — Retrieval híbrido BM25 + dense + RRF

Recuperación por dos vías en paralelo (índice denso existente + BM25 léxico sobre los mismos chunks) fusionadas por Reciprocal Rank Fusion con k=60. Comportamiento observable: queries con términos exactos, jerga o typos leves recuperan chunks que el dense solo no encontraba, sin degradar los casos conceptuales donde v1 acertaba.

**Referencias:** Spec §3 (Retrieval híbrido), ADR-0004 (BM25 stemmer-less multilingüe), ADR-0005 (RRF k=60), ADR-0006 (rerank rechazado), criterio de aceptación Spec §4.

**[Ajuste post-discovery]** El discovery reveló un **chunk imán**: `dashboards-not-loading::1-check-your-internet-connection` domina el top-1 en queries que no le corresponden. La hipótesis es que su fraseo genérico lo hace semánticamente cercano a demasiadas queries. POL-7 debe diagnosticarlo y verificar si el híbrido lo mitiga; la SLI `chunk_dominance_top1_ratio` (umbral > 10% sostenido 30 días, ADR-0005) queda vigilando la recaída.

#### 7.1 Documentar spec del índice BM25

- **Agente:** Watson (Fable 5)
- **Estimado:** 30 min
- **Depende de:** 10.4 (baseline v1 publicado — gate de Plan §4 Fase 1, Principio XII)
- **Criterio de aceptación:** `docs/features/bm25.md` define la tokenización stemmer-less multilingüe (según ADR-0004), la estructura del índice, dónde se persiste y cómo se reconstruye cuando cambia la KB.
- **Jira ID:** —

#### 7.2 Implementar tokenizador + índice BM25

- **Agente:** Opus 5
- **Estimado:** 2h
- **Depende de:** 7.1
- **Criterio de aceptación:** índice BM25 sobre los mismos chunks del índice denso; tests unitarios con términos exactos del producto, jerga del corpus discovery y queries en ES/EN; gobernado por feature flag `V2_HYBRID`.
- **Jira ID:** —

#### 7.3 Documentar spec de la fusión RRF

- **Agente:** Watson (Fable 5)
- **Estimado:** 30 min
- **Depende de:** 7.1
- **Criterio de aceptación:** `docs/features/rrf.md` define la fórmula con k=60, el manejo de empates, el top-K final que entra al prompt de generación y qué pasa cuando una de las dos vías devuelve vacío.
- **Jira ID:** —

#### 7.4 Implementar fusión RRF en el hot path

- **Agente:** Opus 5
- **Estimado:** 1.5h
- **Depende de:** 7.2, 7.3
- **Criterio de aceptación:** dense y BM25 corren en paralelo y se fusionan por RRF tras `V2_HYBRID`; flag off = dense-only v1 intacto; tests de integración de la fusión.
- **Jira ID:** —

#### 7.5 [Ajuste post-discovery] Diagnóstico del chunk imán

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 7.4
- **Criterio de aceptación:** causa raíz del dominio de `dashboards-not-loading::1-check-your-internet-connection` documentada en `bitacora/hallazgos.md` con evidencia (scores comparados antes/después del híbrido); decisión explícita entre reescribir el chunk, ajustar chunking o aceptar y vigilar por SLI. Si la decisión implica re-chunking activo, se respeta el scope freeze del Spec §5 y se difiere con registro.
- **Jira ID:** —

#### 7.6 Tests de integración del retrieval híbrido

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 7.4
- **Criterio de aceptación:** suite cubre: query con término exacto que dense-only fallaba → chunk correcto en top-K; query conceptual donde v1 acertaba → sin degradación; query con typo leve → recupera; flag off = comportamiento v1 byte a byte.
- **Jira ID:** —

#### 7.7 Verificación en sandbox: híbrido vs dense-only

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 7.5, 7.6
- **Criterio de aceptación:** las 30 queries del corpus corridas con flag on y off; comparadas `kb_coverage_pct` y `chunk_dominance_top1_ratio` contra el baseline del discovery (25% de chunks huérfanos, dominancia del chunk imán); resultados en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 7.8 Auditoría Fable del PR

- **Agente:** Fable 5 (auditor externo)
- **Estimado:** 45 min
- **Depende de:** 7.7
- **Criterio de aceptación:** diff auditado contra specs 7.1/7.3, ADR-0004/0005/0006 y Constitution; cero críticos abiertos; hallazgos en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 7.9 Sync a Confluence + cierre

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 7.8
- **Criterio de aceptación:** docs de features en Confluence; worklog derivado de bitácora; POL-7 transicionada a Listo.
- **Jira ID:** —

**Total estimado POL-7: ~8.75h** (9 subtareas; incluye 1h del ajuste post-discovery que v1 del plan no contemplaba).

## POL-8 — Telemetría estructurada + dashboard

Cada request emite un evento con el schema de 27 campos (Plan §3, refinado empíricamente en el discovery) hacia BigQuery vía streaming insert con `waitUntil` (ADR-0002), y un dashboard **Grafana Cloud Free con Dashboard as Code** (ADR-0003) lo consume. Comportamiento observable: el evento aparece en la tabla BQ en menos de un minuto, el dashboard muestra costo/latencia/cache/idiomas/ahorro en tiempo casi real, y un fallo del logger jamás afecta la respuesta al usuario (Principio III).

**Referencias:** Spec §3 (Telemetría + dashboard), Plan §3 (schema 27 campos + métricas derivadas) y §4 Fase 7, ADR-0002 (BQ streaming), ADR-0003 (Grafana + DaC), criterio de aceptación Spec §4.

**[Ajuste de consistencia]** `spec.md` (POL-3) nombra Looker Studio en §3/§4/§6, pero ADR-0003 (POL-4, posterior) lo rechazó — "no versionable como código" — y decidió Grafana Cloud + DaC. `constitution.md` línea 35 arrastra la misma referencia. El ADR gana (decisión de Vlad, 21-ago, hallazgo #1 en `bitacora/hallazgos.md`); la subtarea 8.1 reconcilia los documentos para que ningún lector futuro implemente contra la herramienta rechazada.

#### 8.1 [Ajuste de consistencia] Reconciliar spec.md y constitution.md con ADR-0003

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** —
- **Criterio de aceptación:** las 3 menciones de Looker en `spec.md` (§3, §4, §6) reemplazadas por "dashboard de observabilidad (Grafana Cloud, ADR-0003)"; `constitution.md` línea 35 corregida con bump PATCH + Sync Impact Report actualizado según la convención del patrón Constitution; ambos cambios espejados a Confluence en el sync de cierre (8.12).
- **Jira ID:** —

#### 8.2 Documentar spec de telemetría

- **Agente:** Watson (Fable 5)
- **Estimado:** 45 min
- **Depende de:** 8.1
- **Criterio de aceptación:** `docs/features/telemetry.md` congela el schema de 27 campos (copiado de Plan §3, no reinterpretado), documenta la semántica de `waitUntil` (el insert nunca bloquea la respuesta), el manejo de fallo del sink (`error_stage = bq_sink`, respuesta intacta), qué NO se persiste (texto crudo de query/respuesta, listas completas de chunks — con el porqué), y el kill-switch `TELEMETRY_ENABLED`.
- **Jira ID:** —

#### 8.3 Crear dataset + tabla BQ con DDL versionado

- **Agente:** Sonnet 5
- **Estimado:** 45 min
- **Depende de:** 8.2
- **Criterio de aceptación:** DDL en `observability/bq/events.sql` (versionado en repo, Principio VII); tabla `polaris-triage-demo.polaris_prod_events.events` creada en `us-central1` con partición por `timestamp`; `event_id` documentado como `insertId` de dedup; insert de prueba manual verificado.
- **Jira ID:** —

#### 8.4 Implementar auth de service account (JWT) en el Worker

- **Agente:** Opus 5
- **Estimado:** 2h
- **Depende de:** 8.2
- **Criterio de aceptación:** `worker/auth/bq_jwt.js` firma JWT y obtiene access token con cache del token en KV hasta su expiración (Principio VI — cache antes de compute); tests unitarios de firma y expiración; la credencial vive en secret de Wrangler, nunca en el repo.
- **Jira ID:** —

#### 8.5 Implementar emitEvent() + wiring waitUntil + feature flag

- **Agente:** Opus 5
- **Estimado:** 2h
- **Depende de:** 8.3, 8.4
- **Criterio de aceptación:** `worker/telemetry.js` construye el evento con los 27 campos y lo emite vía `ctx.waitUntil()`; gobernado por `TELEMETRY_ENABLED` (off = cero llamadas a BQ); un fallo del insert se traga con log y `error_stage`, nunca burbujea al usuario.
- **Jira ID:** —

#### 8.6 Tests de integración del sink

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 8.5
- **Criterio de aceptación:** suite cubre: evento aterriza en BQ < 1 min (criterio Spec §4); fallo simulado de BQ no altera la respuesta al usuario; flag off = cero interacción; campos nullable (`intent_*`, `top1_*` cuando `route != kb_grounded`) llegan como NULL y no como valores inventados.
- **Jira ID:** —

#### 8.7 Documentar spec del dashboard

- **Agente:** Watson (Fable 5)
- **Estimado:** 30 min
- **Depende de:** 8.2
- **Criterio de aceptación:** `docs/features/dashboard.md` define los widgets mínimos (costo 24h, latencia p50/p95 por componente, cache hit rate, distribución de intents, distribución de idiomas de query y respuesta, ahorro estimado real-vs-contrafactual, volumen de requests) más las 2 métricas derivadas empíricas (`kb_coverage_pct`, `chunk_dominance_top1_ratio` — Plan §3), el SQL agregado de cada una, y el layout DaC (`observability/dashboards/*.json`).
- **Jira ID:** —

#### 8.8 Conectar Grafana Cloud a BQ + dashboards as code

- **Agente:** Opus 5
- **Estimado:** 2h
- **Depende de:** 8.6, 8.7
- **Criterio de aceptación:** Grafana Cloud Free conectado a BQ como datasource; dashboards versionados en `observability/dashboards/*.json` e importables sin edición manual; todos los widgets de 8.7 poblados con datos reales del entorno dev; link compartible generado (para el portafolio).
- **Jira ID:** —

#### 8.9 Simular pico de carga para poblar el dashboard

- **Agente:** Sonnet 5
- **Estimado:** 1h
- **Depende de:** 8.8
- **Criterio de aceptación:** script Python en `scripts/` genera tráfico sintético variado (idiomas, cache hits/misses, fuera de dominio) contra dev; el dashboard muestra el pico; costo del experimento registrado en `bitacora/hallazgos.md` (referencia: discovery costó USD 0.00283).
- **Jira ID:** —

#### 8.10 Auditoría de re-ataque en runtime (telemetría)

- **Agente:** Opus 5 _(no Fable: framing adversarial dispara safeguards; encuadre "verificación de seguridad de mi propio sistema, en sandbox, autorizada")_
- **Estimado:** 45 min
- **Depende de:** 8.6
- **Criterio de aceptación:** verificado que ninguna PII ni texto crudo de query llega a BQ (solo hashes); que un atacante no puede inflar el costo de BQ vía flood de requests (el budget/kill-switch cubre el caso); que el token JWT cacheado en KV no es legible desde el path del usuario; hallazgos y mitigaciones en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 8.11 Auditoría Fable del PR

- **Agente:** Fable 5 (auditor externo)
- **Estimado:** 45 min
- **Depende de:** 8.9, 8.10
- **Criterio de aceptación:** diff completo auditado contra specs 8.2/8.7, ADR-0002/0003, Plan §3 (schema sin campos fantasma ni renombres silenciosos) y Constitution; cero críticos abiertos; hallazgos en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 8.12 Sync a Confluence + cierre

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 8.11
- **Criterio de aceptación:** docs de features + reconciliación 8.1 reflejados en Confluence bajo el árbol del Plan técnico; worklog derivado de bitácora registrado en Jira; Historia POL-8 transicionada a Listo.
- **Jira ID:** —

**Total estimado POL-8: ~12.5h** (12 subtareas; la Historia más pesada de v2 — es el sustrato de medición del que dependen las afirmaciones de mejora de todas las demás).

## POL-9 — Multilingual explícito (+ modo cliente, Fase 6)

Detección de idioma antes de canonicalize, retrieval cross-lingual contra la KB completa, y respuesta **siempre** en el idioma del query original — incluyendo cuando el sistema dice "no sé" (bug empírico `es-06`). Comportamiento observable: una pregunta en español sobre un artículo en inglés se responde en español con cita al chunk fuente en inglés.

Este bloque absorbe además la **Fase 6 del Plan (modo cliente)**: `spec.md` §3 la describe como comportamiento observable pero sin Historia asignada (hallazgo #3, decisión de Vlad 21-ago). Ambos trabajos editan el mismo artefacto — `worker/prompts/system_v2.md` — y juntarlos evita dos PRs pisando el mismo archivo.

**Referencias:** Spec §3 (Multilingual explícito + Respuestas en modo cliente), Plan §4 Fases 3 y 6, Constitution Principio XIV (multilingual by default), Discovery hallazgo #5 (bug idioma en refusals), criterio de aceptación Spec §4.

**[Ajuste post-discovery]** El discovery detectó un bug real: en la query `es-06` (español), el LLM respondió el "no sé" **en inglés** — cae al idioma del prompt del sistema cuando no cita evidencia. La instrucción de idioma debe ser explícita e incluir refusals y clarificaciones, no un implícito. La subtarea 9.3 lo resuelve y la 9.8 lo convierte en caso de regresión permanente del eval.

#### 9.1 Documentar spec del contrato multilingüe

- **Agente:** Watson (Fable 5)
- **Estimado:** 30 min
- **Depende de:** 10.4 (baseline v1 publicado — gate de Plan §4 Fase 1)
- **Criterio de aceptación:** `docs/features/multilingual.md` define: detección de idioma (dónde ocurre en el hot path, qué pasa si falla → fallback a idioma de la KB con registro), el contrato "respuesta en el idioma del query INCLUYENDO refusals", interacción con el cache (el idioma es parte de la key — Plan §4 Fase 4), y los casos edge (query mixto, idioma no soportado por la KB).
- **Jira ID:** —

#### 9.2 Implementar detección de idioma en el Worker

- **Agente:** Opus 5
- **Estimado:** 1.5h
- **Depende de:** 9.1
- **Criterio de aceptación:** `worker/language.js` detecta ISO 639-1 del query antes de canonicalize; gobernado por `V2_MULTILINGUAL` (off = comportamiento v1 intacto); tests unitarios con los 30 queries del corpus discovery (10 ES + 10 EN + typos); el resultado alimenta `query_lang_detected` de la telemetría.
- **Jira ID:** —

#### 9.3 [Ajuste post-discovery] Instrucción explícita de idioma en el prompt (incluye refusals)

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 9.1
- **Criterio de aceptación:** `worker/prompts/system_v2.md` instruye explícitamente "respond in the same language as the customer question, including refusals and clarifications"; verificado contra el caso `es-06` real: query en español fuera de cobertura recibe el "no tengo información" en español; cero regresión en respuestas grounded.
- **Jira ID:** —

#### 9.4 [Fase 6 — modo cliente] Documentar spec del modo cliente

- **Agente:** Watson (Fable 5)
- **Estimado:** 30 min
- **Depende de:** 9.1
- **Criterio de aceptación:** `docs/features/modo-cliente.md` define el registro objetivo (lenguaje del usuario final, sin jerga interna salvo nombres exactos de features, sin referencias meta tipo "según mis fuentes", estructura corta orientada a acción), los ejemplos few-shot a incluir, y el test de aceptación "pegable en chat de soporte sin edición".
- **Jira ID:** —

#### 9.5 [Fase 6 — modo cliente] Implementar prompt v2 con modo cliente + few-shot

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 9.3, 9.4
- **Criterio de aceptación:** `system_v2.md` integra las instrucciones de modo cliente con las de idioma (9.3) sin contradicción entre sí; gobernado por `V2_MODE_CLIENTE` (flag independiente de `V2_MULTILINGUAL`, Plan §5); flag off = prompt v1 byte a byte.
- **Jira ID:** —

#### 9.6 [Fase 6 — modo cliente] Validación manual de 10 respuestas

- **Agente:** Watson (Fable 5) — Vlad valida, Watson asiste
- **Estimado:** 45 min
- **Depende de:** 9.5
- **Criterio de aceptación:** 10 respuestas generadas con el prompt v2 revisadas una a una contra el criterio "pegable en chat de soporte sin edición" (Spec §4); resultado por respuesta (pasa/no pasa + motivo) en `bitacora/hallazgos.md`; ≥ 8/10 pasan o el prompt se itera antes de cerrar.
- **Jira ID:** —

#### 9.7 Ajustar UI del cliente para cita cross-lingual

- **Agente:** Sonnet 5
- **Estimado:** 45 min
- **Depende de:** 9.2
- **Criterio de aceptación:** la UI muestra la cita al chunk fuente aunque esté en idioma distinto al de la respuesta (Plan §4 Fase 3), sin romper el layout actual; verificado con el caso ES→EN en dev.
- **Jira ID:** —

#### 9.8 Casos multilingües + regresión es-06 al corpus de eval

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 9.3
- **Criterio de aceptación:** el corpus de eval (POL-10) incorpora: queries en ≥ 2 idiomas sobre los mismos temas, y el caso permanente "query en cualquier idioma sobre tema fuera de KB → respuesta en el idioma del query" (regresión del bug es-06).
- **Jira ID:** —

#### 9.9 Verificación en sandbox

- **Agente:** Opus 5
- **Estimado:** 45 min
- **Depende de:** 9.5, 9.7, 9.8
- **Criterio de aceptación:** corpus completo corrido en dev con flags on: idioma de respuesta == idioma del query en el 100% de los casos (grounded Y refusals); citas cross-lingual visibles; flags off = v1 intacto; resultados en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 9.10 Auditoría Fable del PR

- **Agente:** Fable 5 (auditor externo)
- **Estimado:** 45 min
- **Depende de:** 9.6, 9.9
- **Criterio de aceptación:** diff auditado contra specs 9.1/9.4, Principio XIV y Constitution; especial atención a contradicciones entre instrucciones de idioma y de registro en el prompt combinado; cero críticos abiertos; hallazgos en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 9.11 Sync a Confluence + cierre

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 9.10
- **Criterio de aceptación:** docs de features en Confluence; worklog derivado de bitácora; POL-9 transicionada a Listo.
- **Jira ID:** —

**Total estimado POL-9: ~8.5h** (11 subtareas; ~2.5h corresponden al sub-bloque de modo cliente absorbido de la Fase 6).

## POL-10 — Eval framework + baseline (partido en A y B)

Una sola Historia en Jira, **dos ventanas de ejecución** (decisión de Vlad 21-ago, hallazgo #2): el Plan §4 ya la partía implícitamente — "POL-10 (parcial)" en la Fase 1 y "POL-10 (completa)" en la Fase 8. **POL-10.A es el gate de todo v2**: ninguna Historia de implementación (POL-6/7/9/11) arranca hasta que el baseline v1 esté publicado, porque ninguna medición vale sin baseline (Principio XII). POL-10.B es la última pieza antes del cierre: la comparación v1 vs v2 que congela los targets cuantitativos que la Spec §4 dejó como TBD deliberado.

Comportamiento observable: cada PR de v2 adjunta la salida del eval con delta contra baseline (un PR sin eval no se mergea), y las release notes de v2 traen la tabla comparativa final.

**Referencias:** Spec §3 (Eval framework + baseline) y §4 (criterio + política de PR), Plan §4 Fases 1 y 8, Constitution Principio XII (eval-driven), Discovery (corpus semilla de 30 queries + traces).

### POL-10.A — Framework + baseline v1 (Fase 1 — GATE)

#### 10.1 Documentar spec del eval framework

- **Agente:** Watson (Fable 5)
- **Estimado:** 45 min
- **Depende de:** —
- **Criterio de aceptación:** `docs/features/eval.md` define: métricas (Recall@1, Recall@5, Precision@5, MRR, latencia p50/p95, costo promedio), formato del corpus etiquetado (query + idioma + chunks esperados + tipo de respuesta esperada), cómo corre local sin depender del Worker vivo (Spec §4), y el formato del reporte de delta que se adjunta a cada PR.
- **Jira ID:** —

#### 10.2 Construir corpus etiquetado (30-50 queries)

- **Agente:** Opus 5
- **Estimado:** 1.5h
- **Depende de:** 10.1
- **Criterio de aceptación:** corpus en `src/eval/corpus/` con 30-50 queries multiidioma etiquetadas con chunks esperados; las 30 del discovery como semilla (ya tienen traces reales); cubre: típicas ES/EN, typos/jerga, fuera de dominio, ambiguas; el etiquetado de "chunk esperado" se hace contra la KB actual de 52 chunks, no contra la expandida.
- **Jira ID:** —

#### 10.3 Implementar el framework en src/eval/

- **Agente:** Opus 5
- **Estimado:** 2h
- **Depende de:** 10.1, 10.2
- **Criterio de aceptación:** framework Python corre el corpus contra una configuración dada (v1 dense-only o v2 con flags) y reporta las métricas de 10.1; salida en formato tabla pegable en PR; reproducible con un solo comando documentado en el README del módulo.
- **Jira ID:** —

#### 10.4 Correr baseline v1 + publicar

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** 10.3
- **Criterio de aceptación:** `specs/001-polaris-v2/baseline.md` publica las métricas de v1 (dense-only, KB 52 chunks) sobre el corpus completo, con fecha, configuración exacta y costo del experimento; **este documento es el gate**: su existencia desbloquea 6.1, 7.1, 9.1 y 11.1.
- **Jira ID:** —

#### 10.5 Auditoría Fable del PR (framework + baseline)

- **Agente:** Fable 5 (auditor externo)
- **Estimado:** 45 min
- **Depende de:** 10.4
- **Criterio de aceptación:** diff auditado contra spec 10.1 y Principio XII; especial atención a métricas mal implementadas (un baseline con Recall mal calculado invalida TODAS las comparaciones posteriores de v2 — es el error más caro del proyecto); cero críticos abiertos; hallazgos en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 10.6 Sync a Confluence + cierre parcial

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 10.5
- **Criterio de aceptación:** doc del framework + baseline en Confluence; worklog derivado de bitácora; POL-10 queda **En curso** en Jira (no Listo — falta 10.B) con comentario explicando el split.
- **Jira ID:** —

**Subtotal POL-10.A: ~6.5h** (6 subtareas).

### POL-10.B — Comparación final v1 vs v2 (Fase 8)

#### 10.7 Correr eval sobre v2 completo + tabla comparativa

- **Agente:** Opus 5
- **Estimado:** 1h
- **Depende de:** cierre de POL-6, POL-7, POL-8, POL-9 y POL-11
- **Criterio de aceptación:** eval corrido sobre v2 con todos los flags on, sobre el mismo corpus del baseline (más los casos agregados en 9.8, marcados como post-baseline); tabla comparativa v1 vs v2 con delta por métrica; sin regresión en los casos donde v1 acertaba.
- **Jira ID:** —

#### 10.8 Congelar targets cuantitativos con justificación empírica

- **Agente:** Watson (Fable 5)
- **Estimado:** 45 min
- **Depende de:** 10.7
- **Criterio de aceptación:** los TBD de Spec §4 quedan congelados con número y justificación de por qué ese umbral y no otro (compromiso explícito de la Spec); registrados en `spec.md` vía PR (bump de versión del spec) y reflejados en las release notes.
- **Jira ID:** —

#### 10.9 Release notes v2 con tabla comparativa

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 10.8
- **Criterio de aceptación:** release notes públicas (EN — Principio XIII) con la tabla v1 vs v2, los targets congelados y links al dashboard; pegadas al release/tag de v2 en GitHub.
- **Jira ID:** —

#### 10.10 Auditoría Fable del PR

- **Agente:** Fable 5 (auditor externo)
- **Estimado:** 30 min
- **Depende de:** 10.9
- **Criterio de aceptación:** verificado que la tabla no sobreafirma (deltas reales, sin cherry-picking de métricas), que los targets tienen justificación y que las release notes no prometen lo que el dashboard no muestra; cero críticos; hallazgos en `bitacora/hallazgos.md`.
- **Jira ID:** —

#### 10.11 Sync a Confluence + cierre POL-10

- **Agente:** Sonnet 5
- **Estimado:** 30 min
- **Depende de:** 10.10
- **Criterio de aceptación:** tabla y targets en Confluence; worklog derivado de bitácora; POL-10 transicionada a Listo.
- **Jira ID:** —

**Subtotal POL-10.B: ~3.25h** (5 subtareas).

**Total estimado POL-10: ~9.75h** (11 subtareas en dos ventanas: A abre v2, B lo cierra).

## POL-11 — KB expansion

_A completar en commit siguiente._

## Resumen

_A completar en commit siguiente — total estimado, gráfico de dependencias, camino crítico._
