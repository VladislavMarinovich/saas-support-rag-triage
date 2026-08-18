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

_A completar en commit siguiente._

## 4. Fases de ejecución

_A completar en commit siguiente._

## 5. Integración con el Worker actual

_A completar en commit siguiente._

## 6. Convenciones del proyecto

_A completar en commit siguiente._

## 7. Referencias cruzadas

_A completar en commit siguiente._
