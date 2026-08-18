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

_A completar en commit siguiente._

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
