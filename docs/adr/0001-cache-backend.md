# ADR-0001 — Backend de cache para queries canonicalizadas

- **Estado:** Aceptado
- **Fecha:** 2026-08-18
- **Owner:** Vladislav Marinovich · Marinovich Consulting SAS
- **Refs:** [Constitution](../../.specify/memory/constitution.md) principios VI (cache antes de compute), X (latency SLO), I (single-cloud). [POL-3 Spec](../../specs/001-polaris-v2/spec.md) sección 3, feature Canonicalize + cache (POL-6).

## Contexto

Polaris v2 introduce un cache persistente en la capa edge para queries repetidas por distinto fraseo. El cache mapea `hash(query_canonicalizada + idioma) → respuesta_completa`. Requisitos derivados de Constitution y Spec:

- Latencia p95 de hits sensiblemente por debajo del path completo (Principio X — p95 total < 2 s).
- Compartido globalmente entre todas las instancias del Worker.
- TTL configurable, default 24 h.
- Volumen esperado en demo: < 10k entradas activas; potencialmente miles en producción real.
- Cero infra fuera de Cloudflare (Principio I — single-cloud, single-identity).

## Opciones consideradas

**A. Cloudflare KV (Workers KV).** Store key-value distribuido globalmente. Diseñado para read-heavy caching. Reads con eventual consistency, latencia típica en edge ~10 ms. Writes con propagación global ~60 s. Free tier: 100k reads/día, 1k writes/día, 1 GB. Value máx: 25 MB.

**B. Cloudflare D1.** Base SQL relacional en edge. Overkill para el shape key-value; latencia fuera de región primaria degrada; SQL no aporta valor sobre este caso de uso.

**C. Cloudflare Durable Objects.** Storage per-object con consistencia fuerte. Más caro; más código; consistency fuerte no es necesaria para cache read-heavy.

**D. Cloudflare Cache API (Workers Cache).** Cache HTTP per-datacenter. Sub-milisegundo local, pero NO es global — cada datacenter tiene su propio cache aislado. Insuficiente como store primario.

**E. Cloudflare R2.** Object storage tipo S3. Diseñado para blobs grandes; latencia > KV; no es hot-path.

**F. KV + Cache API (dos niveles).** L1 (Cache API per-datacenter) sub-ms + L2 (KV global) ~10 ms. Optimización estándar en CDNs modernos.

## Decisión

**Cloudflare KV como único backend de cache en v2.**

Se descarta la opción F (dos niveles) para v2. Aunque técnicamente superior en latencia, agrega complejidad de código y coordinación entre capas que no aporta valor demostrable para un demo. La latencia de ~10 ms por hit KV en edge es adecuada para el SLO de p95 < 2 s del path completo.

## Estructura de la key

```
key = <version_prefix> ":" sha256(canonicalized_query + ":" + lang_detected)
```

- `version_prefix` inicial: `v2.0`. Permite invalidación en bloque al cambiar KB o modelo: incrementar a `v2.1` deja el cache viejo huérfano; auto-expira por TTL sin necesidad de wildcard delete (KV no lo soporta).
- `canonicalized_query`: salida del prompt de canonicalize (POL-6). Idioma-agnóstica en su forma canónica.
- `lang_detected`: código ISO 639-1 (`es`, `en`, `pt`, ...) obtenido de la detección explícita del query.

## Estructura del value

JSON con schema estable:

```json
{
  "response_text": "...",
  "citations": [
    { "chunk_id": "kb-42", "title": "...", "section": "..." }
  ],
  "language": "es",
  "generated_at": 1755551234,
  "cost_hint": { "embed": 0.00003, "gen": 0.00018, "canonicalize": 0.00001 }
}
```

El campo `cost_hint` alimenta el widget de ahorro estimado del dashboard (Spec sección 3 POL-8, sección 6 métricas post-launch).

## TTL policy

- **Default: 24 h.** Baseline razonable para KB de producto SaaS sin cambios diarios.
- **TTL escalonado por hash** para mitigar cold-cache masivo:
  - Los 4 bits menos significativos del hash determinan un offset entre 0 y 15 h.
  - TTLs efectivos distribuidos uniformemente entre 24 h y 39 h.
  - Evita la avalancha "todos expiran a las 24 h en punto" tras un evento de tráfico alto.

## Invalidación

- No hay invalidación selectiva. KV no soporta wildcard delete.
- Invalidación en bloque vía `version_prefix` en la key. Al deploy que cambie KB, prompt o modelo, se incrementa el prefix; el cache viejo queda huérfano y auto-expira por TTL.
- No hay UI de "borrar mi cache" para el usuario final. No aplica al caso de uso.

## Consecuencias

**Positivas:**

- Latencia p95 en hits: ~10 ms en edge global. Dentro del SLO holgadamente.
- Cero infra externa a Cloudflare. Coherente con single-cloud (Principio I).
- Free tier de KV cubre el volumen esperado del demo entero (100k reads/día).
- Código simple: una capa de cache, sin coordinación L1/L2.

**Negativas / trade-offs aceptados:**

- Eventual consistency de KV: entre el write y la propagación global (~60 s), otros datacenters pueden ejecutar path completo aunque la respuesta ya existe. Aceptado: mejor eventual consistency que sobre-diseño para strong consistency.
- Sin invalidación fina. Aceptado: caso de uso no lo requiere.
- No se demuestra el patrón L1+L2 al reviewer. Aceptado: la simplicidad es la decisión correcta para el demo; el ADR documenta que la alternativa fue evaluada. Si en v2.1+ el volumen o los patrones de tráfico lo justifican, se reabre este ADR.

## Costo

- Free tier de Workers KV: 100k reads/día, 1k writes/día, 1 GB storage — cubre el demo.
- Escalado paid: $0.50 por millón reads, $5 por millón writes. Volumen esperado en producción hipotética hace que el gasto en KV sea marginal frente al ahorro en llamadas a Vertex AI.

## Métricas de vigilancia

| SLI (campo del schema BQ + widget dashboard) | Umbral que dispara reevaluación | Acción |
|---|---|---|
| **`cache_hit_rate`** — porcentaje de requests que hicieron hit en KV (exact + canonicalized). Widget: gauge. | < 20% durante 30 días con volumen sostenido > 100 req/día. | Reabrir POL-6 (canonicalize). Prompt de canonicalización posiblemente no está normalizando lo suficiente, o la KB cambia demasiado rápido invalidando writes. |
| **`kv_write_error_rate`** — porcentaje de escrituras a KV que fallan. Widget: time series. | > 1% durante 7 días. | Revisar quotas del free tier (1k writes/día) o migrar a plan pago. Si es error de auth, rotar credenciales. |
| **`cache_serve_latency_p95`** — latencia p95 servido desde KV en hits. Widget: stat. | > 30 ms sostenido durante 7 días. | Investigar región del KV o considerar activar Layer 1 (Cache API) — reabrir la opción F descartada aquí. |
| **`kv_reads_per_day`** — volumen de reads/día contra el free tier cap de 100k. Widget: bar chart. | > 80k reads/día durante 3 días. | Alerta preventiva: patrón L1+L2 empieza a rendir. Presupuestar migración o activar L1 Cache API. |
