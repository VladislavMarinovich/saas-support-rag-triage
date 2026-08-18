<!-- Sync Impact Report: v0.0.0 → v1.0.0 (MAJOR: constitution inicial). Enmienda POL-1: se crea la Constitución de Polaris con 14 principios fundamentales que gobiernan el proyecto durante el ciclo v2 (canonicalize + hybrid + telemetría + multilingual + eval + KB expandida). Motivación: fijar bases filosóficas ANTES de codificar para tener criterio de aceptación/rechazo de PRs, evitar scope creep (regla operativa v(N+1)) y encodear prácticas senior demoables a reviewers USD. Templates dependientes creados: docs/WORKFLOW.md, .github/pull_request_template.md. -->

# Constitución Polaris

**Polaris**: SaaS Support Triage + Analytics con RAG grounded sobre KB de producto. Runtime Cloudflare Workers + Vertex AI. Flagship AI Engineer portfolio de Marinovich Consulting.

## Principios Fundamentales

### I. Enterprise-first, single-cloud, single-identity

Todo pasa por Vertex AI + Cloudflare + una service account. Cero AWS, cero fragmentación multi-provider.
- Embeddings, generación y logging en Vertex.
- Deploy y edge en Cloudflare.
- Un solo principal (service account) autentica embed + gen + BQ.
- Nuevas dependencias que rompen single-cloud requieren ADR con justificación fuerte.

**Justificación**: Simplifica auditoría, contratos y respuesta a incidentes. Es el patrón que compran las empresas grandes. Diferenciador vs demos multi-cloud que se ven fragmentadas.

### II. Grounded > creative

El LLM responde EXCLUSIVAMENTE con evidencia de la KB. Cero alucinación tolerada.
- Si los chunks recuperados no contienen la respuesta, el LLM debe decir "no lo sé" honestamente.
- El prompt del sistema prohíbe explícitamente inventar contenido fuera de los excerpts.
- Cada respuesta debe poder rastrearse a chunks específicos (ver Principio XI).

**Justificación**: Trust del usuario final + defensa en interviews ("nuestro RAG no alucina porque el prompt lo prohíbe explícitamente y las respuestas citan fuentes").

### III. Observability by default

Cada request emite un evento a BigQuery con métricas completas: costo (tokens embed/gen/canonicalize), latencia por componente, intent detectado, chunks recuperados, cache hit/miss, feedback del usuario.
- Sin excepciones. Un endpoint sin telemetría no se mergea.
- `waitUntil()` para no bloquear la respuesta al usuario con el insert BQ.
- Feature flag para cortar telemetría si BQ falla — el hot path nunca depende del logger.

**Justificación**: Base para eval-driven decisions (XII), cost control (IV) y dashboards demoables (Looker).

### IV. Cost cap explícito

`LIVE=false` kill-switch obligatorio. Cada llamada Vertex tiene budget diario declarado en Wrangler. Al superarlo, el endpoint responde `demo_paused` (503) sin llamar a Vertex.
- Alertas de budget al 50% / 80% / 100%.
- Nunca comprometer más de $50/mes en demo pública sin decisión explícita del owner.
- Simulaciones de carga usan datos sintéticos, no requests reales al Worker LIVE.

**Justificación**: Vlad no tiene margen para $500 sorpresa al mes. La demo pública siempre debe tener freno de mano.

### V. ML clásico donde funciona; LLM solo donde aporta

La clasificación de labels (topic/type/priority/routing/sentiment) puede ser LogReg o XGBoost — no requiere LLM caro. El LLM se reserva para generación de respuesta y canonicalization de query.
- Cada uso de LLM debe justificar por qué ML clásico no basta.
- LLM como fallback cuando ML tiene baja confianza es válido; LLM como default no lo es.

**Justificación**: Latencia menor (ms vs s), costo 1000× menor, determinismo, portafolio ML puro. No usar LLM como martillo universal.

### VI. Cache antes de compute

Query del usuario → canonicalize (Gemini Flash Lite barato) → hash SHA-256 → check Cloudflare KV.
- Si hit, respuesta directa desde cache.
- Si miss, cadena completa de RAG y se guarda en KV con TTL 24h.
- Cache key incluye idioma detectado para evitar cruces multilingüe erróneos.

**Justificación**: 30-60% de queries en soporte SaaS son duplicados con distinto fraseo. Ahorro directo en $$$ y latencia. Simple, defendible en interviews.

### VII. PHVA riguroso

Todo cambio pasa por: rama `feature/POL-XX-descripcion` → PR → squash-merge → cierre issue Jira → worklog → doc Confluence.
- Sin push directo a `main`. La convención es la ley porque técnicamente no hay branch protection en GitHub Free privado.
- Conventional Commits obligatorio en el commit final del squash.
- `Refs POL-XX` en el body de cada commit.

**Justificación**: Trazabilidad completa. Cualquier reviewer USD puede recorrer cada línea de código hasta su Historia Jira y su decisión en Confluence.

### VIII. Portafolio-driven

Cada decisión técnica debe justificarse por (a) skill USD demoable y/o (b) valor real para usuario final. No overengineering por completitud ni por diversión.
- Cada Historia Jira responde: ¿qué skill demuestra esto en interview? ¿qué gana el usuario final?
- Features que no responden ninguna se rechazan.

**Justificación**: Tiempo es escaso. Un feature que no habla directo a un job description o a un usuario, se descarta.

### IX. Graceful degradation

Cuando algo falla, degradar en cascada elegante:
- Cache miss → LLM completo.
- LLM timeout → mensaje canned + escalate.
- Embed error → BM25 solo.
- Todo falla → mensaje amigable + ticket auto-escalado.

Nunca dejar al usuario con un `error 500`.

**Justificación**: Sistemas resilientes son statement técnico senior. Ningún reviewer premia un pipeline frágil.

### X. Latency SLO explícito

`p95 < 2 segundos` end-to-end para respuesta al usuario. Toda decisión arquitectónica se somete a este número duro.
- Cache hits deben responder en `p95 < 100ms`.
- Cada componente reporta su latencia individual a la telemetría (III).
- Un cambio que empeora p95 se rechaza salvo justificación mayor.

**Justificación**: Convierte decisiones subjetivas ("¿agregamos rerank?") en objetivas ("¿el rerank mantiene p95 < 2s?"). Portafolio-friendly.

### XI. Source-cited answers

Cada respuesta muestra los chunks usados (título del artículo KB + sección + confianza). El usuario puede verificar cada afirmación.
- Formato en la UI: `📚 Fuente: [Título del artículo] → Sección: [Heading]`.
- Los chunk IDs se persisten en telemetría (III) para auditoría posterior.

**Justificación**: Diferenciador vs ChatGPT genérico. Refuerza principio II (grounded). Base para trust de enterprise buyers que preguntan "¿cómo sabemos que no inventa?".

### XII. Eval-driven — no PR sin eval

Todo cambio de retrieval, prompt o modelo se mide contra baseline con el eval framework (queries + expected chunks).
- Sin comparación cuantitativa, no se mergea.
- Baseline vive en el repo; cada release actualiza métricas.
- Métricas mínimas: Recall@1, Recall@5, Precision@5, MRR.

**Justificación**: Convierte "creo que mejora" en "mejora +7% recall@5 vs baseline". Es lo que diferencia ML Engineer real de Software Engineer que agrega features al azar.

### XIII. Bilingüe estratificado (interno vs público)

Regla de idioma por audiencia:
- Código, comentarios, Jira, Confluence, ADRs, docs internas → **español**.
- README público del repo, descripción GitHub, landing, papers → **inglés**.

**Justificación**: Coherente con el resto del stack de Marinovich Consulting (regla dura #1 con excepción estratificada). Team = español. Mundo externo = inglés.

### XIV. Multilingual by default (producto)

El producto opera cross-lingual sin ceremonia:
- Query en cualquier idioma matchea contra KB en cualquier idioma (embeddings `text-embedding-005` son multilingual nativos).
- Respuesta se genera en el idioma del query original (detectado automáticamente en canonicalize).
- BM25 arranca stemmer-less; se especializa por idioma si eval lo justifica.

**Justificación**: Statement técnico ("RAG avanzado, no básico"). Bajo costo (los modelos ya soportan multilingual). Prueba de concepto que después se aplica en Wiggins.

## Distinción clave XIII vs XIV

| Principio | Alcance | Ejemplo |
|---|---|---|
| **XIII · Bilingüe estratificado** | Cómo escribimos código/docs internas vs externas | Comentarios en español, README en inglés |
| **XIV · Multilingual by default** | Cómo el PRODUCTO trata idiomas del usuario final | Usuario escribe en español → producto responde en español |

Son complementarios, no redundantes.

## Flujo de Trabajo

**Cadena de trazabilidad integral**:
- Constitution → Spec funcional → Plan técnico + ADRs → Tasks → branch `feature/POL-XX-desc` → commits con `Refs POL-XX` → PR con link Jira → squash-merge → cierre Jira → worklog → doc Confluence.

**Ciclo PHVA por cambio**:
1. **Planear**: Issue padre en Jira + descomponer en subtareas + ubicar el código afectado.
2. **Hacer**: Cambio atómico; si falta dependencia, abre subtask con mini-PHVA.
3. **Verificar**: Probar en devapp/local sobre casos afectados. Correr eval framework (XII).
4. **Actuar**: Commit + push con key correcto + cerrar subtask + cerrar padre + documentar en Confluence + worklog.

**Regla operativa — Scope freeze v(N+1)**:
Cuando un scope está congelado (Spec, Plan, Tasks aprobados para vN), toda idea nueva que surja durante la ejecución se etiqueta como **v(N+1)** y se difiere al backlog. No se agrega al scope activo. Primero terminar v(N), después evolucionar.

## Formato de referencia a principios

Los 14 principios se refieren **por número romano** en:
- Descripciones de Historias Jira ("Cumple III, X, XII").
- Descripciones de PR ("Este cambio implementa VI y respeta IV").
- ADRs cuando una decisión balancea 2 principios en tensión.
- Reviews de código — el reviewer puede rechazar citando el número.

## Gestión y Documentación

- Source of truth: este archivo (`.specify/memory/constitution.md`) en el repo.
- Confluence espeja este contenido con nota "auto-generado desde repo — no editar acá".
- Cambios entran por PR contra este archivo, nunca directo en Confluence.
- Cada cambio actualiza el Sync Impact Report al inicio.

## Cambios a la Constitución

Modificar, agregar o remover un principio requiere:
1. ADR explícito documentando la razón (`docs/adr/ADR-XXX-cambio-constitucion.md`).
2. Aprobación del owner (Vlad Marinovich).
3. Actualización del Sync Impact Report al inicio de este archivo con versión bump (SemVer: MAJOR = principio eliminado o reescrito, MINOR = principio agregado, PATCH = clarificación).
4. Actualización de Confluence espejo con `versionMessage` claro.
5. Announcement en el Home Polaris.

No se cambia la Constitución "porque parece buena idea". Se cambia cuando la realidad demuestra que un principio no aguantó.

## Gobernanza

**Autoridad**: Vladislav Marinovich, owner de Marinovich Consulting SAS y del repo Polaris.

**Conflictos**: La Constitución es la ley. Cuando el código contradice la Constitución, gana la Constitución y el código se corrige. Cuando la Spec contradice la Constitución, se reescribe la Spec. El código es la última capa; la Constitución es la primera.

## Historial de versiones

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0.0 | 2026-08-18 | Constitución inicial con 14 principios. Base del Spec Kit v2. |

**Autoría**: Vladislav Marinovich · Marinovich Consulting SAS · ops@marinovich.co
