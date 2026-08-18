# ADR-0002 — Sink de telemetría al backend de análisis

- **Estado:** Aceptado
- **Fecha:** 2026-08-18
- **Owner:** Vladislav Marinovich · Marinovich Consulting SAS
- **Refs:** [Constitution](../../.specify/memory/constitution.md) principios III (observability by default), IX (graceful degradation), I (single-cloud). [POL-3 Spec](../../specs/001-polaris-v2/spec.md) sección 3, feature Telemetría estructurada + dashboard (POL-8).

## Contexto

Cada request al Worker de Polaris debe emitir un evento estructurado con métricas de costo, latencia por componente, intent, chunks recuperados, cache hit/miss, idiomas, y estado del sistema. Los eventos son la materia prima del dashboard (POL-8) y del análisis empírico que decide targets cuantitativos (POL-10).

Requisitos derivados de Constitution y Spec:

- El insert al sink **NO puede bloquear** la respuesta al usuario (Principio III).
- Fallo del sink **NO puede tumbar** el hot path (Principio IX — degradación elegante).
- Los eventos deben aterrizar en el backend en menos de un minuto para permitir observabilidad casi en tiempo real.
- Kill-switch para cortar la telemetría sin redeploy (feature flag).
- Cero infra fuera de la nube nativa (Principio I).

## Opciones consideradas

**A. BQ Streaming Insert directo desde el Worker con `waitUntil`.** El Worker termina de responder al usuario, luego dentro de `ctx.waitUntil()` ejecuta un `fetch` HTTPS al endpoint `insertAll` de BigQuery. Auth vía service account JSON almacenado como Wrangler secret; el Worker genera JWT, lo intercambia por access token, y cachea el token en KV por ~1 hora.

**B. Cloudflare Queues + Worker consumidor → BQ.** El Worker de request publica el evento a una Queue Cloudflare. Un segundo Worker consume la Queue en batches y hace inserts a BQ. Absorbe picos, permite retry natural con backoff, mejor backpressure.

**C. Cloudflare Analytics Engine + sync periódico a BQ.** Analytics Engine es el storage nativo de Cloudflare para eventos de alto volumen. Cuota generosa y muy barato. Un job periódico (Worker con cron trigger) sincroniza a BQ para análisis rico.

**D. Google Cloud Pub/Sub → Dataflow → BQ.** Patrón Google-nativo para streaming pipelines. Máxima resiliencia y throughput, pero requiere infra Dataflow y no es single-cloud (introduce dos servicios GCP nuevos).

## Decisión

**Opción A: BQ streaming insert directo desde el Worker con `waitUntil`.**

Es la más simple, coherente con single-cloud (todo GCP para storage/análisis + Cloudflare para runtime), y suficiente para el volumen esperado. Un demo de portafolio no genera el tráfico que justifica Queues o Pub/Sub.

## Diseño

**Flujo por request:**

1. Worker recibe request → procesa cadena RAG completa (canonicalize, cache lookup, retrieval, generación).
2. Worker construye el evento en memoria: JSON con los ~25 campos definidos en `specs/001-polaris-v2/discovery/bq-schema.md` (schema derivado empíricamente en Fase 0 del Plan).
3. Worker responde al usuario final. Latencia percibida: la del path completo, sin costo adicional por telemetría.
4. Dentro de `ctx.waitUntil(sendToBQ(event))`, el Worker ejecuta el insert. Se corre en background, extendiendo la vida del Worker sin bloquear la respuesta ya enviada.

**Autenticación a BQ:**

- Service account JSON completo almacenado como `wrangler secret put BQ_SA_JSON`.
- Al primer insert de la instancia, el Worker firma JWT con la private key del service account (RS256, header con `kid`, claims con `iss`, `scope=https://www.googleapis.com/auth/bigquery.insertdata`, `aud=https://oauth2.googleapis.com/token`).
- Intercambia JWT por access token en `https://oauth2.googleapis.com/token`.
- Cachea el access token en KV con TTL de 55 minutos (Google los emite con expiración de 1h).
- Requests subsecuentes leen el token de KV, evitando el ciclo JWT en cada evento.

**Endpoint de insert:**

```
POST https://bigquery.googleapis.com/bigquery/v2/projects/polaris-triage-demo/datasets/polaris_prod_events/tables/events/insertAll
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "rows": [
    { "insertId": "<uuid>", "json": { ...event fields... } }
  ]
}
```

`insertId` deduplica en el lado de BQ dentro de una ventana de un minuto; útil si `waitUntil` reintenta por transitorios.

**Feature flag:**

`TELEMETRY_ENABLED` en Wrangler env. Si `false`, el Worker omite el `waitUntil(sendToBQ)` completo. Permite cortar telemetría en incidentes sin redeploy.

**Manejo de errores:**

- Si el fetch a BQ falla (timeout, 5xx, auth error), el error se atrapa dentro del promise de `waitUntil` y se descarta.
- Se emite un `console.error` para que aparezca en Cloudflare Workers Logs.
- Best-effort: el evento se pierde. No hay retry en v2. Documentado como trade-off aceptado.
- El usuario final NUNCA se entera. El hot path ya respondió antes del intento de insert.

## Consecuencias

**Positivas:**

- Cero infra nueva: dos servicios ya presentes (Cloudflare Workers + BQ existente en `polaris-triage-demo`).
- Latencia percibida por usuario: cero impacto (waitUntil se ejecuta tras response).
- Costo: negligible en demo. BQ streaming insert cobra $0.010 por 200 MB insertados; el volumen esperado en demo es < 1 MB/día.
- Simple de razonar: un solo path, un solo API call, sin colas ni consumidores.
- Coherente con Principio I (single-cloud storage/análisis) y Principio III (observability by default).

**Negativas / trade-offs aceptados:**

- **Pérdida potencial de eventos** ante fallo de BQ o timeout. Sin retry, sin dead-letter queue. Aceptado: para portafolio la exhaustividad del log no es crítica; para producción real se reevalúa.
- **Sin batching**: cada request = un insert = un API call. A volúmenes altos esto sube el costo lineal. Aceptado: al volumen del demo, insignificante.
- **Sin backpressure**: si BQ está saturado, el Worker no lo sabe hasta que el insert falla. Aceptado: BQ streaming rara vez satura para nuestro perfil de tráfico.
- **Auth vía service account JSON como secret**: la private key vive en Cloudflare Workers secrets. Compromiso del stack Cloudflare compromete el acceso BQ. Aceptado: mitigación es rotar la key periódicamente y limitar el scope del service account a `bigquery.dataEditor` sobre el dataset `polaris_prod_events` únicamente.

## Métricas de vigilancia

| SLI (campo del schema BQ + widget dashboard) | Umbral que dispara reevaluación | Acción |
|---|---|---|
| **`bq_insert_success_rate`** — porcentaje de eventos que aterrizaron exitosamente en BQ (medido con contador dual: requests con `waitUntil` disparado vs filas efectivas insertadas comparadas por ventana). Widget: gauge. | < 99.5% durante 7 días. | Revisar auth (JWT expiration, service account permisos), quotas de BQ, errores en Cloudflare Workers Logs. |
| **`waitUntil_hang_p95`** — latencia p95 del `waitUntil(sendToBQ)` medido desde emisión hasta ack de BQ. Widget: time series. | > 3 s p95 durante 7 días. | Cloudflare mata Workers a los 30 s de inactividad; latencias altas indican riesgo de eventos perdidos por corte del Worker. Considerar retry con timeout más agresivo o migrar a Queues (opción B). |
| **`telemetry_flag_off_duration`** — tiempo acumulado con `TELEMETRY_ENABLED=false` fuera de ventanas de mantenimiento programado. Widget: stat. | > 4 h por día sin justificación en el log de operaciones. | Alerta a owner: se están perdiendo datos sin notarlo. Reactivar flag o documentar razón. |
| **`bq_insert_volume_daily`** — eventos insertados por día vs proyección de tráfico. Widget: time series comparativo. | Volumen cae > 30% respecto al promedio móvil de 30 días sin caída correspondiente en tráfico del Worker. | Indica pérdida silenciosa de eventos. Investigar canal BQ o auth. |

## Referencias

- Cloudflare Workers `waitUntil`: [developers.cloudflare.com/workers/runtime-apis/context/#waituntil](https://developers.cloudflare.com/workers/runtime-apis/context/#waituntil).
- BigQuery streaming inserts: [cloud.google.com/bigquery/docs/streaming-data-into-bigquery](https://cloud.google.com/bigquery/docs/streaming-data-into-bigquery).
- Google OAuth 2.0 Service Account: [developers.google.com/identity/protocols/oauth2/service-account](https://developers.google.com/identity/protocols/oauth2/service-account).
- ADR-0001 (cache backend) — mismo patrón de auth via KV para access tokens.
