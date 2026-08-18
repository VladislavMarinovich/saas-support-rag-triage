# ADR-0003 — Herramienta de dashboard de observabilidad

- **Estado:** Aceptado
- **Fecha:** 2026-08-18
- **Owner:** Vladislav Marinovich · Marinovich Consulting SAS
- **Refs:** [Constitution](../../.specify/memory/constitution.md) principios III (observability by default), VIII (portafolio-driven), VII (PHVA — todo cambio pasa por PR). [POL-3 Spec](../../specs/001-polaris-v2/spec.md) sección 3, feature Telemetría estructurada + dashboard (POL-8). [ADR-0002](0002-sink-telemetria.md) — los eventos aterrizan en BigQuery.

## Contexto

v2 necesita un dashboard vivo que consuma los eventos BQ y presente costo, latencia p50/p95 por componente, cache hit rate, distribución de intents e idiomas, ahorro estimado, y otros derivados. El dashboard sirve dos propósitos: monitoreo por el owner y demostración pública en el portafolio.

Requisitos derivados:

- Consumir BigQuery como datasource sin infra intermedia.
- Widgets ricos: time series, stat, gauge, table, distribuciones categóricas.
- Real-time o near-real-time (refresh manual o cada X minutos aceptable — no exige sub-segundo).
- Compartible públicamente vía link para portafolio.
- Versionable en repo (Principio VII — todo cambio pasa por PR; también aplica a dashboards).
- Coherente con Constitution Principio I (single-cloud gestionable) — aceptar SaaS externo si aporta el valor sin fragmentar operación.

## Opciones consideradas

**A. Looker Studio (Google).** Nativo del ecosistema GCP, gratis, conector BQ integrado. Sin curva de aprendizaje. Desventaja: widgets básicos, no diseñado para observability técnica, no versionable como código, dashboards no exportables como texto.

**B. Grafana Cloud Free Tier + Dashboard as Code (JSON en repo).** SaaS gestionado por Grafana Labs. Free tier: 10k active series, 50 GB logs, 14 días retención, 3 usuarios, plugin BigQuery oficial. Dashboards se serializan como JSON, se versionan en el repo, se aplican vía UI Import o script `curl` a la API. Estándar de facto en observability senior.

**C. Grafana Cloud + Terraform provider (IaC completo).** Dashboards, alertas y data sources declarados en HCL, aplicados con `terraform apply`. Máxima disciplina de infraestructura como código.

**D. Grafana Cloud + Grafonnet (Jsonnet).** Dashboards generados programáticamente en Jsonnet. Muy potente para dashboards muchos y repetitivos. Curva alta, adopción baja fuera de círculos SRE muy avanzados.

**E. Self-host Grafana OSS (Oracle Cloud Free Tier + Cloudflare Tunnel).** Zero-trust arquitectónico, statement fuerte de "opero mi propia infra". Descartado por evento externo: Oracle rechazó el signup por política de tarjetas virtuales (común en LATAM). Documentado en `memory/reference_oracle_cloud_free_tier.md`.

**F. Cloudflare Analytics Engine + built-in charts.** Nativo del stack, cero infra externa. Limitación fuerte: 32 dimensiones máximo por schema, widgets pobres, no cubre el caso multi-dimensional del schema de v2.

## Decisión

**Opción B: Grafana Cloud Free Tier + Dashboard as Code (JSON en repo).**

Ubicación del stack: **US East (Ohio)** — la región Grafana Cloud más cercana geográficamente a `us-central1` (Iowa), donde vive Vertex AI del proyecto `polaris-triage-demo` y donde se creará el dataset BQ. Latencia intra-US entre Grafana y BQ esperada ~15–20 ms.

## Diseño

**Estructura en el repo:**

```
observability/
  dashboards/
    polaris-overview.json         # dashboard principal (costo, latencia, cache, idiomas)
    polaris-cost-detail.json      # (posible) detalle de costos + ahorro
  README.md                        # cómo importar / desplegar
  scripts/
    deploy-dashboards.sh           # POST a Grafana Cloud API
```

**Flujo de cambio (PHVA aplicado a dashboards):**

1. **Planear:** issue en Jira (POL-8 o subtask).
2. **Hacer:** editar JSON directamente en el editor, o exportar desde la UI de Grafana (Share → Export → Save to file) y committear.
3. **Verificar:** importar en un dashboard de staging dentro del mismo stack (folder `staging/`) y confirmar renderiza.
4. **Actuar:** PR contra `main`, review, rebase-and-merge (por WORKFLOW.md), `scripts/deploy-dashboards.sh` empuja a producción.

**Autenticación del script de deploy:**

Grafana Cloud API token con scope `dashboards:write` almacenado como secret en el entorno donde se ejecute (local `.env` gitignored, GitHub Actions secret si se automatiza). Endpoint: `POST https://<stack>.grafana.net/api/dashboards/db` con el JSON del dashboard en el body.

**Conexión a BigQuery:**

Plugin oficial de Grafana Labs para BigQuery. Auth vía service account key JSON pegado en la configuración del datasource (UI), o vía OAuth interactivo del owner. Recomendación: service account con scope de solo lectura sobre el dataset `polaris_prod_events`. La misma cuenta se puede reutilizar del proyecto `polaris-triage-demo`.

**Público / privado:**

Free tier permite **Public Dashboards** — un dashboard puede exponerse vía URL pública sin login. El plan es exponer un subconjunto (dashboard de overview con métricas agregadas) como link público para el portafolio. Se mapea a custom domain `grafana.marinovich.co` para presentación.

## Consecuencias

**Positivas:**

- **Statement de portafolio:** Grafana es el estándar de facto en observability senior. Un reviewer USD que abra el repo y vea `observability/dashboards/*.json` lee inmediatamente "este señor entiende Dashboard as Code y GitOps aplicado a monitoring". Diferenciador vs demos que solo tienen dashboards en la UI sin versionar.
- **Coherente con Principio VII:** todo cambio de dashboard entra por PR, es revisado, es reproducible.
- **Cero infra propia:** Grafana Labs mantiene el runtime; nosotros mantenemos los dashboards como código.
- **Costo cero** dentro del Free tier para el volumen del demo.
- **Real-time suficiente:** refresh configurable de 5s a manual; near-real-time efectivo.
- **Widgets ricos** cubren todos los tipos declarados en la Spec (stat de ahorro, time series de costos, gauges de cache hit, distribuciones categóricas de intents e idiomas, tabla de últimos requests).
- **Alertas nativas** con webhooks (Slack, email) sin código extra — cubre el requisito de "alertas de budget al 50%/80%/100%" de la Spec sección 7.
- **Portabilidad:** si mañana migramos a Grafana OSS self-host, los JSON funcionan igual sin cambios.

**Negativas / trade-offs aceptados:**

- **Trial de 14 días** con features Enterprise activadas por default. Post-trial baja a Free tier automáticamente. Se documenta para evitar sorpresas.
- **URL del stack autogenerada** (`swiftporridge960.grafana.net`) — el subdomain no se renombra fácilmente en Free tier. Mitigación: custom domain `grafana.marinovich.co` vía CNAME al finalizar v2 antes de publicación pública.
- **Dependencia de SaaS externo.** Si Grafana Cloud tiene downtime, los dashboards no se ven. Aceptado: los datos están en BQ (single source of truth); Grafana es solo la vista.
- **Los JSON de Grafana no son diff-friendly** — tienen campos como `id` y `version` que cambian con cada save. Mitigación: `deploy-dashboards.sh` normaliza el JSON (borra IDs volátiles) antes de commit, o se usa un pre-commit hook. Detalle operativo, no bloqueante.
- **IaC completo (Terraform / Grafonnet) descartado en v2.** Para 1-2 dashboards y ~15 paneles, Dashboard as Code por JSON es proporcional; Terraform sería sobre-ingeniería. Se reevalúa en v2.1 si el volumen de dashboards crece.

## Cuándo revisitar este ADR

- Se pasa de 2 dashboards a 5+ (empieza a pesar el mantenimiento manual del JSON).
- Se necesita gestionar data sources, alertas y folders también como código.
- El equipo crece a > 3 personas editando dashboards (Terraform aporta review en HCL).
- Grafana Cloud Free tier deja de cubrir el volumen y hay que pasar a self-host.

## Referencias

- Grafana Cloud Free Tier: [grafana.com/products/cloud/](https://grafana.com/products/cloud/).
- Plugin BigQuery datasource: [grafana.com/grafana/plugins/grafana-bigquery-datasource/](https://grafana.com/grafana/plugins/grafana-bigquery-datasource/).
- Grafana HTTP API dashboards: [grafana.com/docs/grafana/latest/developers/http_api/dashboard/](https://grafana.com/docs/grafana/latest/developers/http_api/dashboard/).
- Public Dashboards: [grafana.com/docs/grafana/latest/dashboards/dashboard-public/](https://grafana.com/docs/grafana/latest/dashboards/dashboard-public/).
- ADR-0002 — la fuente de datos que Grafana consume vive en BigQuery.
