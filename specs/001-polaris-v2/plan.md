<!-- Plan técnico Polaris v2 — POL-4. Fuente de verdad. Confluence espeja al cierre. -->

# Polaris v2 — Plan técnico

**Versión:** DRAFT (POL-4 en curso)
**Autor:** Vladislav Marinovich · Marinovich Consulting SAS
**Refs:** Constitution v1.0.0 (`../../.specify/memory/constitution.md`), [Spec funcional](spec.md), 6 ADRs en [`../../docs/adr/`](../../docs/adr/).

Este documento describe CÓMO se implementa Polaris v2. La Spec dice qué se construye y por qué; los ADRs justifican cada decisión atómica; este plan los une en una arquitectura ejecutable con fases claras.

## 1. Statement arquitectónico

Polaris v2 no es un ejercicio técnico aislado. Es un intento deliberado de construir un sistema de RAG que un ingeniero senior USD reconozca como *auditable, operable, y mantenible por alguien que no lo construyó*. Esa aspiración se traduce en tres compromisos que gobiernan cada decisión de este plan.

**Observability by design, no logging por precaución.** El schema de eventos se deriva bottom-up desde preguntas concretas de negocio — ¿dónde está el sobrecosto?, ¿el sistema alucina?, ¿en qué idiomas preguntan?, ¿el ahorro del cache es real? — traducidas a SLIs verificables. Los campos que se emiten existen porque responden esas preguntas, no porque estén disponibles. Cada campo que no responde una pregunta se descarta.

**Sistema que sobrevive al arquitecto.** Cada ADR de Polaris incluye una sección explícita de métricas de vigilancia con SLI + umbral concreto + acción definida. Cuando un umbral se cruza, cualquier operador que llegue meses después abre el dashboard, ve la alerta, lee el ADR asociado, y sabe qué hacer. No necesita entender la historia del proyecto, no necesita conocer al autor, no necesita adivinar por qué la decisión se tomó así. El sistema se explica solo, se defiende solo, y pide ser reabierto solo cuando el mundo bajo sus pies cambia.

**Preparación para experimentación futura.** Las decisiones de v2 son informed guesses respaldadas por criterio arquitectónico, no A/B tests. Con el volumen actual de un demo no hay señal estadística para experimentar rigurosamente. Pero la infraestructura de observabilidad que se construye en v2 — schema estructurado, telemetría no bloqueante, dashboards versionados, métricas de vigilancia — es exactamente el sustrato que habilita A/B testing cuando llegue el volumen. Cada campo del schema es una variable que mañana se podrá segmentar por variante.

Estos tres compromisos se materializan a lo largo del plan. Todo lo demás es implementación.


## 2. Arquitectura general

La arquitectura de Polaris v2 se documenta visualmente en el artefacto vivo **[Anatomía de Polaris](https://claude.ai/code/artifact/c7f8f9c2-19db-4b28-8600-e4b9262f1c09)** con tres diagramas complementarios: contexto (bloques y vecinos), ejecución (secuencia de un request completo), y observabilidad (viaje del evento del Worker al panel). Este plan describe en prosa lo que esos diagramas muestran.

El sistema tiene una capa de runtime, una capa de storage caliente, una capa de storage analítico, y una capa de visualización. Cada una vive en el proveedor donde su costo y su latencia son óptimos, y las cuatro se conectan por HTTPS estándar sin infra intermedia.

**Capa de runtime.** El Polaris Worker corre en el edge global de Cloudflare, expuesto en `polaris.marinovich.co`. La misma imagen del Worker atiende cualquier request de cualquier región del mundo, ejecutándose en el datacenter más cercano al usuario. Dentro del Worker viven: el pipeline de canonicalización (llamada corta a Gemini Flash Lite), la lógica de cache lookup contra KV, el módulo BM25 con el índice invertido en memoria, la orquestación de retrieval híbrido con RRF, y el prompt de generación grounded contra chunks recuperados.

**Capa de storage caliente.** Cloudflare Workers KV mantiene el cache de respuestas canonicalizadas, con TTL escalonado por hash entre 24 y 39 horas (ADR-0001). KV vive globalmente distribuido en el edge de Cloudflare, con latencia de lectura ~10 ms desde cualquier Worker.

**Capa de storage analítico.** BigQuery en `us-central1` (Iowa) recibe los eventos vía streaming insert directo desde el Worker, ejecutado en `waitUntil` para no bloquear la respuesta al usuario (ADR-0002). El dataset `polaris_prod_events` vive en la misma región donde vive Vertex AI del proyecto `polaris-triage-demo`, lo que elimina egress inter-region y aprovecha la vecindad para consultas rápidas.

**Capa de visualización.** Grafana Cloud Free Tier hospedado en US East (Ohio), la región Grafana más cercana geográficamente a `us-central1`. Los dashboards son artefactos JSON versionados en `observability/dashboards/*.json` del repo (ADR-0003). Un subconjunto se expone públicamente vía la funcionalidad Public Dashboards, y se mapea a `grafana.marinovich.co` con CNAME para presentación de portafolio.

**Servicios externos.** Vertex AI en `us-central1` provee embeddings (`text-embedding-005`) y generación (`gemini-2.5-flash-lite`). Es el único servicio pagado en la ruta caliente y el que dispara el kill-switch cuando el budget se toca.

**Coherencia del diseño.** Cloudflare para runtime y storage caliente, Google Cloud para inferencia y storage analítico, Grafana Labs para dashboards. Tres proveedores, cada uno para lo que hace mejor. La Constitution (Principio I) no exige un único cloud absoluto; exige coherencia y no fragmentación gratuita. Este diseño la cumple.


## 3. Schema BigQuery draft

El schema de la tabla `polaris_prod_events` en `polaris-triage-demo.polaris_prod_events.events` se declara aquí como **draft**. El schema definitivo se congela al cerrar la Fase 0.b (discovery observacional del flow actual), documentada en `specs/001-polaris-v2/discovery/bq-schema.md`. Los campos listados abajo son la hipótesis actual derivada de las preguntas de negocio establecidas en la Spec y de la conversación técnica al planear v2.

Cada campo se agrupa por bloque lógico. Las preguntas de negocio que cada bloque responde están indicadas para trazabilidad.

**Identidad del evento — ¿de qué request estamos hablando?**

| Campo | Tipo | Descripción |
|---|---|---|
| `event_id` | STRING | UUID generado en el Worker. Sirve como `insertId` en BQ para deduplicación. |
| `timestamp` | TIMESTAMP | Instante de finalización del request. |
| `session_hash` | STRING | Hash SHA-256 del session ID (o IP + user agent, sin PII). Permite detectar re-preguntas del mismo usuario sin identificarlo. |

**Query — ¿qué pidió el usuario?**

| Campo | Tipo | Descripción |
|---|---|---|
| `query_hash` | STRING | Hash de la query original. Para dedup sin persistir el texto. |
| `query_length` | INT64 | Longitud del texto original en caracteres. |
| `query_lang_detected` | STRING | ISO 639-1 detectado por canonicalize. |

**Cache — ¿el cache está sirviendo o no?**

| Campo | Tipo | Descripción |
|---|---|---|
| `cache_hit_type` | STRING | Enum: `miss`, `exact_hit`, `canonicalized_hit`. |

**Clasificación e intent — ¿qué tipo de pregunta era?**

| Campo | Tipo | Descripción |
|---|---|---|
| `intent_predicted` | STRING | Intent inferido por el clasificador. |
| `intent_confidence` | FLOAT64 | Score/probabilidad del intent predicho. |

**Routing — ¿a dónde fue esa pregunta?**

| Campo | Tipo | Descripción |
|---|---|---|
| `route` | STRING | Enum: `kb_grounded`, `escalate_human`, `canned_fallback`. |
| `kb_section` | STRING | Sección/tema principal del artículo KB usado. Nullable si `route != kb_grounded`. |

**Retrieval — ¿qué se recuperó y qué tan seguros estamos?**

| Campo | Tipo | Descripción |
|---|---|---|
| `top1_score` | FLOAT64 | Score RRF del chunk top-1. |
| `top5_avg_score` | FLOAT64 | Promedio de scores RRF de los top-5. |
| `top3_chunk_ids` | STRING (repeated) | IDs de los 3 chunks más relevantes. |

**Generación — ¿respondió con evidencia o dijo "no sé"?**

| Campo | Tipo | Descripción |
|---|---|---|
| `grounded_answer` | BOOL | `true` si citó al menos un chunk, `false` si respondió "no sé" honesto. |
| `response_lang` | STRING | ISO 639-1 del idioma de la respuesta generada. |
| `response_length_tokens` | INT64 | Tokens de la respuesta al usuario. |

**Costo — ¿cuánto costó este request y cuánto habría costado sin cache?**

| Campo | Tipo | Descripción |
|---|---|---|
| `cost_embed_usd` | FLOAT64 | Costo del embedding en USD. `0` en cache hits. |
| `cost_canonicalize_usd` | FLOAT64 | Costo del canonicalize en USD. |
| `cost_gen_usd` | FLOAT64 | Costo de generación en USD. `0` en cache hits. |
| `tokens_input` | INT64 | Tokens totales enviados a Vertex. |
| `tokens_output` | INT64 | Tokens totales recibidos de Vertex. |
| `cost_hypothetical_full_path_usd` | FLOAT64 | Costo estimado si el mismo request hubiera ejecutado el path completo. Habilita el widget de ahorro estimado. |

**Latencia — ¿dónde se van los milisegundos?**

| Campo | Tipo | Descripción |
|---|---|---|
| `latency_total_ms` | INT64 | Tiempo total desde recepción hasta respuesta enviada. |
| `latency_canonicalize_ms` | INT64 | Solo el paso de canonicalize. |
| `latency_cache_lookup_ms` | INT64 | Solo el lookup en KV. |
| `latency_retrieval_ms` | INT64 | BM25 + dense + RRF combinados. |
| `latency_gen_ms` | INT64 | Solo la generación. |

**Estado del sistema — ¿en qué contexto operaba Polaris cuando pasó esto?**

| Campo | Tipo | Descripción |
|---|---|---|
| `live_state` | BOOL | `true` si el kill-switch estaba activo permitiendo llamadas Vertex. |
| `path_taken` | STRING | Enum: `full`, `bm25_only`, `canned_fallback`. Registra degradación elegante (Principio IX). |
| `error_stage` | STRING | Nullable. Si hubo error, indica en qué etapa: `embed`, `retrieval`, `gen`, `bq_sink`. |

**Total:** 26 campos. Volumen esperado en demo: < 1 MB/día. Almacenamiento en BQ trivial (~$0.02/mes).

**Lo que deliberadamente NO se guarda.** No se persiste el texto crudo de la query ni de la respuesta (PII potencial). No se guardan las listas completas de chunks recuperados (cardinalidad explosiva). No se guardan tokens individuales del LLM (nivel de granularidad no accionable). Estas exclusiones se documentan aquí para que ningún colaborador futuro las agregue "por si acaso" y contamine el schema.


## 4. Fases de ejecución

La implementación de v2 se ejecuta en nueve fases ordenadas por dependencia real, no por numeración de Historias Jira. El orden respeta el principio de que ninguna medición vale sin baseline, y ninguna optimización se activa antes de que haya un evento que optimizar.

**Fase 0 — Preparación y discovery.**
Cierra el Spec Kit y descubre empíricamente el schema definitivo antes de tocar infraestructura pesada. Sub-fases:
- 0.a. Cerrar POL-3 (Spec) y POL-4 (Plan + ADRs). *Estado: en curso.*
- 0.b. Discovery observacional: instrumentar el Worker actual con logs temporales, correr 30 queries variadas, capturar traces en `specs/001-polaris-v2/discovery/traces.jsonl` en formato XES-lite para permitir process mining futuro.
- 0.c. Diseño de taxonomías (intents, modelo de clasificación) desde los traces reales.
- 0.d. Schema BQ definitivo en `specs/001-polaris-v2/discovery/bq-schema.md` derivado de la observación.
- 0.e. Crear dataset `polaris_prod_events` en BQ `us-central1`, namespace KV en Cloudflare, service accounts. Verificar permisos.

**Fase 1 — Baseline de v1 con eval framework.**
Historia relacionada: POL-10 (parcial).
Ninguna mejora tiene sentido sin baseline. Se implementa el eval framework en `src/eval/`, se define corpus etiquetado de 30-50 queries en varios idiomas con chunks esperados y respuestas esperadas, se corre el framework contra v1 (dense-only, KB actual) y se publica el baseline en `specs/001-polaris-v2/baseline.md`.

**Fase 2 — KB expansion.**
Historia relacionada: POL-11.
Se expande la KB a 60-100 artículos manteniendo la estructura H2 actual. Se re-chunkean, se re-embedean con `text-embedding-005` (mismo modelo — ADR pertinente indica no cambiar en v2), se actualiza el índice denso del Worker, y se re-corre el eval sobre la KB expandida para verificar que el retrieval no degrada por dilución.

**Fase 3 — Multilingual explícito.**
Historia relacionada: POL-9.
Se agrega detección de idioma en el Worker antes de canonicalize. Se actualiza el prompt del sistema para instruir explícitamente responder en el idioma del query. Se agregan queries multilingüe al corpus de eval. Se ajusta la UI del cliente para mostrar cita al chunk fuente aunque esté en otro idioma que la respuesta.

**Fase 4 — Canonicalize + cache.**
Historia relacionada: POL-6. ADR asociado: 0001.
Se diseña el prompt de canonicalize (Flash Lite, output < 20 tokens), se implementa el hash SHA-256 sobre la forma canónica más el idioma detectado, se integra el KV lookup antes del retrieval. TTL escalonado por hash entre 24 y 39 horas. Se instrumenta `cache_hit_type` como campo del evento.

**Fase 5 — Retrieval híbrido BM25 + dense + RRF.**
Historia relacionada: POL-7. ADRs asociados: 0004, 0005.
Se implementa el tokenizer BM25 stemmer-less multilingual. Se construye el índice BM25 offline en Python y se exporta como JSON bundled en el Worker. Se implementa la función de scoring BM25 en el Worker. Se implementa RRF k=60 sobre top-20 de cada método. La decisión de re-chunking queda abierta hasta ver eval: solo se re-chunkea si los datos lo justifican (Principio VI y XII).

**Fase 6 — Modo cliente en generación.**
Historia relacionada: descrita en Spec sección 3 como comportamiento observable.
Se actualiza el prompt del sistema con instrucción explícita de "modo cliente": lenguaje del usuario final, sin jerga interna del producto salvo términos exactos, sin referencias meta, estructura orientada a acción. Se agregan ejemplos few-shot al prompt. Se validan 10 respuestas manualmente contra el criterio "pegable en chat de soporte sin edición".

**Fase 7 — Telemetría estructurada + dashboard.**
Historia relacionada: POL-8. ADRs asociados: 0002, 0003.
Se implementa la función `emitEvent()` con el schema definitivo. Se envuelve el flow del Worker con `ctx.waitUntil(emitEvent(...))`. Feature flag `TELEMETRY_ENABLED` para kill-switch. Se conecta Grafana Cloud a BigQuery como datasource. Se crean los primeros dashboards versionados en `observability/dashboards/*.json`. Widgets iniciales: costo 24h, latencia p50/p95, cache hit rate, distribución de intents, distribución de idiomas, ahorro estimado, volumen de requests. Se simula pico de carga con script Python para poblar el dashboard sintéticamente.

**Fase 8 — Eval final v1 vs v2.**
Historia relacionada: POL-10 (completa).
Se corre el eval framework sobre el corpus completo comparando v1 (baseline de Fase 1) contra v2 (estado tras Fases 2-7). Se genera tabla comparativa con delta por métrica: Recall@1, Recall@5, Precision@5, MRR, latencia p50/p95, costo promedio. Los targets cuantitativos declarados como TBD en la Spec se congelan aquí con justificación empírica. La tabla se publica en las release notes de v2.

**Fase 9 — Cierre y publicación.**
Se activa `LIVE=true` con budget diario declarado en Wrangler. Se verifican alertas de budget al 50%, 80% y 100%. Se actualiza el README público del repo (en inglés) con el nuevo estado del demo, links al dashboard público de Grafana, y al artefacto "Anatomía de Polaris". Se configura el custom domain `grafana.marinovich.co` vía CNAME. Confluence se sincroniza con el estado final.

**Dependencias entre fases.** La Fase 0 debe cerrar antes que cualquier otra. La Fase 1 (baseline) debe cerrar antes de las Fases 2-6 (para que la comparación tenga sentido). Las Fases 2-6 pueden solaparse parcialmente si se coordina. La Fase 7 requiere el schema definitivo de Fase 0.d. La Fase 8 requiere que todo lo anterior esté congelado. La Fase 9 solo cuando la 8 pasa criterios.

**Timeline estimado.** ~6-8 semanas al ritmo de 10-12 horas/semana declarado para Polaris. Estimado que se refina en POL-5 (Tasks breakdown).


## 5. Integración con el Worker actual

_A completar en commit siguiente._

## 6. Convenciones del proyecto

_A completar en commit siguiente._

## 7. Referencias cruzadas

_A completar en commit siguiente._
