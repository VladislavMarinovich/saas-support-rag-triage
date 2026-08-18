<!-- Spec funcional Polaris v2 — POL-3. Estado: DRAFT. Fuente de verdad: este archivo. Confluence espeja al cierre de POL-3. -->

# Polaris v2 — Especificación funcional

**Versión:** DRAFT (POL-3 en curso)
**Autor:** Vladislav Marinovich · Marinovich Consulting SAS
**Refs:** Constitution v1.0.0 (`.specify/memory/constitution.md`), Epic POL-1.

Este documento describe QUÉ hace Polaris v2 y por qué. No describe cómo — eso vive en el Plan técnico (POL-4).

## 1. Contexto y problema

Polaris v1 es un demo funcional de RAG grounded sobre KB de producto, corriendo en Cloudflare Workers con Vertex AI (embeddings `text-embedding-005` y generación `gemini-2.5-flash-lite`). Responde preguntas de soporte citando fuentes de la KB actual (20 artículos, 89 chunks estructurales por sección H2) y clasifica el ticket antes de generar respuesta.

Cuatro carencias limitan a v1 como flagship de portafolio y como producto real:

**Sin memoria de queries repetidas.** Cada request paga la cadena completa de embed + retrieval + generación, incluso cuando la misma pregunta (o su reformulación) llegó minutos antes. En soporte SaaS, la proporción de queries duplicadas con distinto fraseo es sustancial y se está pagando cada una desde cero.

**Retrieval solo denso.** v1 recupera por similitud semántica únicamente. Las preguntas de usuario tienen errores tipográficos, jerga de producto y nombres exactos de features que un índice denso puro representa peor que un índice léxico. No hay fallback ni fusión.

**Cero observabilidad estructurada.** No se registra costo por request, latencia por componente, intent detectado, chunks recuperados ni cache hit/miss. Sin ese sustrato, cualquier discusión sobre "¿mejoró?" es opinión, no dato — lo que contradice Principio XII (eval-driven).

**Multilingual por accidente.** El modelo de embeddings soporta múltiples idiomas de forma nativa, pero el sistema no lo trata como caso de primera clase: la KB, el prompt y la cadena asumen tácitamente el mismo idioma en query y contenido. No hay contrato explícito ni verificación.

v2 aborda estas cuatro carencias como un solo ciclo cerrado — canonicalización + cache antes de compute, retrieval híbrido, telemetría de primera clase, y multilingual explícito — con un eval framework que respalda cada afirmación de mejora con números contra un baseline.

## 2. Usuarios y jobs-to-be-done

Polaris sirve simultáneamente a tres audiencias con expectativas distintas. La spec optimiza para las tres sin comprometer a ninguna.

**Usuario final — persona que hace la pregunta.** Puede ser un agente de soporte que necesita responder rápido a un cliente, o el propio cliente resolviéndose solo. Su JTBD es *resolver un problema concreto sin leer documentación completa*. Espera una respuesta corta, en su idioma, con lenguaje del usuario y no jerga de producto, y que le indique dónde verificar (fuente citada). No le importa qué modelo la generó ni si hubo cache hit.

**Reviewer USD — persona que evalúa el portafolio.** Es un tech lead o hiring manager mirando el repo para decidir si Vlad es senior L5-L6. Su JTBD es *validar en menos de 10 minutos si este candidato piensa como arquitecto o solo como coder*. Espera ver decisiones justificadas (Constitution + ADRs), métricas contra baseline (eval framework), observabilidad real (dashboard Looker), y un producto que funciona en vivo con costo demostrable. No le impresiona una demo bonita sin telemetría detrás.

**Owner — Vlad como operador del sistema.** Su JTBD es *mantener un demo público que sirve a los dos anteriores sin quemar presupuesto ni acumular deuda técnica silenciosa*. Espera kill-switch confiable, alertas de costo, degradación elegante ante fallos de Vertex, y trazabilidad completa Jira → Confluence → repo → deploy.

El diseño de v2 respeta las tres capas: el usuario final ve respuestas útiles en modo cliente; el reviewer ve el rigor debajo; el owner mantiene el sistema sin sorpresas.

## 3. Alcance funcional v2

Seis features componen v2, descritas como comportamiento observable — no como implementación, que vive en el Plan técnico (POL-4).

**Nota de método sobre telemetría:** el schema de eventos de v2 se diseña bottom-up desde preguntas de negocio concretas (¿dónde está el sobrecosto?, ¿qué componente es el cuello de botella?, ¿el sistema está siendo honesto o alucinando?), traducidas a SLIs verificables. Esas SLIs determinan qué eventos crudos se capturan; no al revés. El detalle empírico del schema sale de una fase de descubrimiento observacional sobre el flow actual, documentada en `specs/001-polaris-v2/discovery/`. Esto es *observability by design*, no logging por precaución.

**Canonicalización + cache (POL-6).** Antes de recuperar y generar, el sistema normaliza la query del usuario a una forma canónica idioma-agnóstica y consulta un cache persistente en la capa edge. Si la forma canónica coincide con una consulta reciente, la respuesta se sirve del cache. Si no, se ejecuta la cadena completa y el resultado se persiste. El cache tiene TTL configurable y respeta el idioma del query original al servir. El comportamiento observable es que dos usuarios haciendo preguntas equivalentes en distinto fraseo reciben la misma respuesta, y la segunda es sensiblemente más rápida.

**Retrieval híbrido (POL-7).** El sistema recupera candidatos por dos vías en paralelo: índice denso (embeddings semánticos) e índice léxico (BM25 sobre los mismos chunks). Los dos resultados se fusionan por Reciprocal Rank Fusion. El comportamiento observable es que queries con términos exactos del producto, jerga interna o errores tipográficos leves recuperan chunks correctos que el índice denso solo no encontraba, y viceversa para queries conceptuales.

**Telemetría estructurada + dashboard (POL-8).** Cada request emite un evento con timestamp, costo por componente (embed + generación + canonicalize), latencia por componente, intent detectado, chunks recuperados, cache hit/miss, idioma detectado y idioma de respuesta. Los eventos aterrizan en BigQuery y alimentan un dashboard en Looker Studio con las métricas anteriores agregadas. El comportamiento observable es que cualquier reviewer puede abrir el dashboard y ver el sistema operando en tiempo casi real, incluyendo simulaciones de picos de carga.

**Multilingual explícito (POL-9).** El sistema detecta el idioma del query, recupera contra la KB completa sin importar el idioma de cada chunk, y responde en el idioma original del query. La KB permanece en su idioma técnico nativo (típicamente inglés para productos SaaS); es el LLM el que traduce en generación. El comportamiento observable es que una pregunta en español sobre un artículo en inglés se responde en español, con cita al chunk fuente en inglés.

**Eval framework + baseline (POL-10).** Existe un conjunto de queries etiquetadas con chunks esperados y respuestas esperadas. El framework corre v1 y v2 sobre el mismo conjunto y reporta Recall@K, Precision@K, MRR, latencia p50/p95 y costo promedio. Ningún PR de v2 se mergea sin correr el framework y adjuntar delta contra baseline. El comportamiento observable es que cada release trae una tabla comparativa en las release notes.

**Respuestas en modo cliente.** El prompt de generación instruye al LLM a responder en lenguaje del usuario final: sin jerga interna del producto salvo cuando el término es el nombre exacto de una feature, sin referencias meta al sistema ("según mis fuentes"), y con estructura corta orientada a acción. La KB permanece técnica; la traducción de registro ocurre en el LLM. El comportamiento observable es que las respuestas se pueden pegar directo en un chat de soporte sin edición.

**Expansión de KB (POL-11).** La KB crece a un tamaño que hace la evaluación estadísticamente más significativa y el retrieval más realista. El comportamiento observable es que preguntas antes fuera de cobertura ahora tienen respuesta grounded.

## 4. Criterios de aceptación

Los criterios cuantitativos de v2 se definen empíricamente en POL-10 tras correr el baseline de v1 sobre el eval framework. Publicar targets antes de tener baseline produce números arbitrarios. Los targets finales se anunciarán en las release notes con justificación de por qué se eligió cada umbral y no otro. Lo que sí queda fijado en esta spec es el criterio cualitativo por feature: qué comportamiento observable debe existir para considerar la feature aceptada.

**Canonicalize + cache.** Dado un usuario que hace una pregunta previamente respondida (misma forma canónica en la ventana TTL), cuando se procesa el request, entonces se sirve del cache con latencia p95 sensiblemente menor a la del path completo. La forma canónica ignora orden de palabras, mayúsculas, puntuación y variantes triviales de fraseo. El idioma del query original se preserva en la respuesta servida por cache.

**Hybrid retrieval.** Dada una query con término exacto de producto o jerga interna que un dense retriever puro miss, cuando se ejecuta el retrieval, entonces el chunk correcto aparece en el top-K fusionado. Dado un query conceptual sin términos exactos, cuando se ejecuta el retrieval, entonces el híbrido no degrada respecto al dense-only en los mismos casos donde v1 acertaba.

**Telemetría + dashboard.** Dado un request cualquiera al Worker, cuando termina de responder, entonces el evento correspondiente aparece en la tabla BigQuery en menos de un minuto. El dashboard Looker muestra al menos: costo total últimas 24h, latencia p50/p95 por componente, cache hit rate, distribución de intents, y volumen de requests. Un fallo del logger no afecta la respuesta al usuario (Principio III).

**Multilingual.** Dado un query en un idioma distinto al mayoritario de la KB, cuando se procesa, entonces el retrieval recupera chunks relevantes sin importar su idioma, y la respuesta se genera en el idioma del query original con cita al chunk fuente en su idioma nativo.

**Eval framework.** Dado un cambio en retrieval, prompt o modelo, cuando se abre un PR, entonces el checklist del PR incluye la salida del eval con delta contra baseline v1. Un PR sin eval no se mergea. El framework corre local sin depender del Worker en vivo.

**Modo cliente.** Dada una respuesta generada por Polaris, cuando un revisor humano la lee, entonces la respuesta pasa el test de "esto se pega en el chat con el cliente sin editar": sin jerga interna, sin referencias meta al sistema, sin verbosidad innecesaria, con estructura orientada a acción.

**KB expansion.** Dada la KB expandida, cuando se ejecuta el eval framework sobre queries de dominio conocido, entonces la cobertura aumenta respecto a la KB de v1 y las métricas de retrieval no degradan significativamente por dilución.

## 5. Fuera de alcance (v2.1+)

Los siguientes items han sido considerados y quedan deliberadamente fuera de v2. La regla operativa de scope freeze v(N+1) aplica: no se debaten ni se agregan hasta cerrar v2.

**Re-embedding con modelo superior** (por ejemplo `gemini-embedding-001` o `text-multilingual-embedding-002`). Cambiarlo en v2 rompe la comparabilidad del baseline y confunde la atribución de mejora. Se evalúa en v2.1 con eval propio.

**Re-chunking activo** más allá del baseline. Queda como decisión empírica dentro de POL-7 o POL-10 si los datos lo justifican; no se rediseña proactivamente.

**Classifier local de labels** (LogReg / XGBoost) reemplazando al LLM en clasificación. Consistente con Principio V pero exige pipeline offline propio, versionado de modelo, y monitoreo de drift — trabajo suficiente para su propia versión.

**HyDE** (Hypothetical Document Embeddings) o query rewriting para retrieval más allá de canonicalize. Suma complejidad y latencia; se evalúa solo si POL-10 muestra retrieval como cuello de botella real.

**Migración a Vector DB dedicada** (Cloudflare Vectorize o similar). Con < 1000 chunks, el índice en memoria en el Worker basta; migrar antes es prematuro.

**Feedback loop del usuario** (thumbs up/down persistidos). Requiere modelo de datos propio y consentimiento; interesante pero secundario a las carencias que resuelve v2.

**Redacción de PII en KB o queries.** No está en el path de un demo de portafolio; se activa cuando haya cliente real con datos sensibles.

**Rerank cross-encoder** entre retrieval y generación. Sujeto a Principio X (p95 < 2s) — solo entra si el margen de latencia lo permite tras medir baseline.

**Clarificación multi-turn** (el sistema pregunta al usuario para desambiguar antes de responder). Rompe el modelo single-turn de v1/v2 y toca cache, telemetría y estado del cliente. La decisión de meterla depende de datos empíricos: si el baseline y las mejoras de v2 (hybrid + canonicalize) resuelven las queries ambiguas por fraseo, clarificación no aporta. Si el dashboard muestra que una fracción significativa de queries llega con retrieval de baja confianza sin importar cuánto se mejora el retrieval, entonces multi-turn se justifica y entra en v2.1 con criterio, no adivinando.

## 6. Métricas post-launch

30 días después del cierre de v2 con LIVE activado en producción, el sistema se considera exitoso si se cumplen las siguientes condiciones observables sobre el dashboard Looker.

**Costo bajo control.** El gasto acumulado en Vertex + BigQuery se mantiene dentro del budget declarado en Wrangler sin activaciones del kill-switch por sobrecosto. Cache hit rate estabilizado por encima del nivel que POL-10 marque como target.

**Latencia dentro de SLO.** p95 end-to-end por debajo de 2 segundos en el path completo (Principio X). p95 en cache hits por debajo de 100 ms.

**Multilingual en uso real.** Al menos dos idiomas distintos aparecen en la distribución de idioma detectado en el dashboard, con métricas de retrieval comparables entre ellos (sin sesgo severo hacia el idioma mayoritario de la KB).

**Eval no regresa.** Cualquier PR mergeado en el mes trae eval adjunto y no degrada Recall@5 ni MRR contra el baseline v2 inicial.

**Uso demoable.** El dashboard es lo suficientemente estable y presentable para que Vlad pueda compartirlo en vivo con un reviewer USD durante una entrevista, sin cirugía previa.

## 7. Riesgos y mitigaciones

Cinco riesgos reales identificados durante Planear. Cada uno con mitigación explícita para que no requiera decisión bajo presión más adelante.

**Costo de BigQuery streaming supera lo previsto.** Aunque el volumen del demo es bajo, `waitUntil` puede acumular inserts si la cardinalidad explota (por ejemplo, chunks recuperados como columna anidada). Mitigación: schema minimalista en el sink, agregación diaria en tabla separada, y alertas de budget al 50% / 80% / 100% del budget diario BQ.

**Cold cache invalida la promesa de latencia.** Si el cache KV está vacío tras un deploy o expira en bloque, la primera oleada de queries paga el path completo y el p95 se degrada temporalmente. Mitigación: TTL escalonado por hash de query (no todos expiran juntos), y warm-up opcional de queries top-N en deploy.

**BM25 stemmer-less degrada en algunos idiomas.** Sin stemming, ciertas familias morfológicas ricas (español, ruso, alemán) pierden matches por variantes flexionales. Mitigación: eval multilingual por idioma; si un idioma cae bajo umbral aceptable en POL-10, se activa stemmer específico solo para él (Principio XIV permite especialización empíricamente justificada).

**Chunk size actual no óptimo para retrieval híbrido.** Los chunks estructurales por sección H2 fueron optimizados para dense; BM25 puede preferir tamaños distintos. Mitigación: la decisión queda abierta, no fijada; el eval framework compara alternativas si los datos lo sugieren.

**Kill-switch flapping.** Si el budget se toca varias veces al día por picos, el estado `LIVE` puede alternar y confundir tanto al usuario como a la telemetría. Mitigación: histéresis en la lógica de activación (una vez cortado, requiere intervención manual para reactivar dentro del ciclo de budget), y estado `demo_paused` explícito en la UI en lugar de error genérico.
