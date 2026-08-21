<!-- Definición del producto ficticio Polaris — borrador PARQUEADO (capturado 2026-08-21 en sesión POL-10.1, decisión de Vlad). Consumidor: subtarea 11.2 (criterios de expansión de KB) y 10.2 (queries con códigos en el corpus de eval). NO es scope de POL-10: los artículos de KB se escriben en POL-11, después del gate del baseline. -->

# Polaris — definición del producto ficticio

**Fuente:** Vlad, 21-ago-2026. Nomenclatura de errores diseñada por Watson por delegación explícita. La KB pública se escribe en inglés (Principio XIII); este doc interno va en español.

## Qué es

**Polaris** es un SaaS de marketing analytics: unifica datos de plataformas de ads y CRM en dashboards, con reportes automatizados, alertas y un agente LLM de soporte (el propio Agentic RAG que estamos construyendo es una feature del producto — el demo ES el producto).

## Módulos

| Módulo | Qué hace | KB actual que lo cubre |
|---|---|---|
| **Dashboards** | Construcción y visualización de métricas | `dashboards-build`, `dashboards-not-loading`, `northstar-define` |
| **Conexiones (connectors)** | Integración con fuentes de datos | `connectors-*` (5 artículos) |
| **Editor** | Edición de dashboards y reportes (asumido de "ediciones" — **confirmar con Vlad**) | — (nuevo en POL-11) |
| **Reportes automatizados** | Programación y envío a destinos (email, Slack) | `reports-schedule`, `reports-not-arriving` |
| **Alertas** | Umbrales sobre métricas → notificación | `alerts-create`, `alerts-not-firing` |
| **Agente LLM (Agentic RAG)** | Asistente de soporte del producto | — (nuevo en POL-11) |
| **Atribución** | Modelos de atribución + UTMs | `attribution-*` (2 artículos) |
| **Usuarios y roles** | Invitaciones, permisos | `users-*` (2 artículos) |

## Planes y conectores

Diferencia entre planes = **número de conexiones** + **qué conectores** (decisión Vlad 21-ago):

| Plan | Conectores | Conexiones |
|---|---|---|
| **Starter** | Google Ads, Meta Ads, Google Analytics, Slack | pocas (definir nº en 11.2) |
| **Growth** | Starter + **CRM (HubSpot)** + **email marketing (Mailchimp)** | intermedias |
| **Enterprise** | Growth + **Salesforce** | máximas |

Slack está en todos los planes (es canal de envío de reportes/alertas, además de conector).

## Nomenclatura de códigos de error

Regla: `XXnnn — Título exacto en inglés` (el título es el nombre del artículo de KB; el código exacto es imán para BM25/POL-7). Familias:

| Familia | Dominio | Ejemplos semilla |
|---|---|---|
| **ER** — Connection & sync | Fallas de conexión/sincronización de conectores | ER001 Authorization expired · ER002 Provider rate limit exceeded · ER003 Invalid credentials · ER004 Sync timeout · **ER005 Not synced with Google Ads** (ejemplo canónico de Vlad) · ER006 Not synced with Meta Ads |
| **PF** — Permissions & access | Usuario/rol sin permiso | PF001 You don't have access to this dashboard · PF002 Role cannot edit · PF003 Connector not available on your plan · PF004 Seat limit reached |
| **PL** — Plan & billing | Límites del plan, facturación | PL001 Connection limit reached · PL002 Upgrade required for this connector · PL003 Payment failed |
| **RP** — Reports delivery | Reportes automatizados y envío | RP001 Report delivery failed · RP002 Invalid destination · RP003 Report generation timed out |
| **AL** — Alerts | Alertas | AL001 Alert did not fire · AL002 Notification channel unreachable |
| **DB** — Dashboards & data | Visualización y frescura de datos | DB001 Dashboard failed to load · DB002 Widget shows no data · DB003 Data freshness delayed |
| **AG** — Assistant (agente LLM) | El propio agente | AG001 Assistant unavailable · AG002 Question outside knowledge base |

Los códigos concretos y sus artículos se escriben en **11.3** (uno por código, estructura H2 self-contained: Symptom / Cause / Fix). Esta tabla es la semilla, no el catálogo cerrado.

## Uso inmediato (10.2 — corpus de eval)

2-3 queries con códigos (ej. *"me aparece ER005 y no sincroniza con google ads"*, *"what does PF003 mean"*) entran al corpus etiquetadas `fuera_de_dominio` contra la KB actual (los artículos no existen aún). Al cerrar POL-11 se re-etiquetan a sus artículos nuevos — la mejora queda medida.
