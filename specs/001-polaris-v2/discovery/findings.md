# Discovery — Hallazgos empíricos

Este documento consolida los hallazgos del discovery observacional (Fase 0.b del Plan técnico v2). Se corrió el hot path v1 en Python contra Vertex AI real con 30 queries variadas, capturando traces por etapa en formato XES-lite. Complementa `summary.md` (métricas agregadas) con análisis dirigido a decisiones concretas del schema BQ y de los ADRs.

**Fecha:** 2026-08-19
**Corpus:** 30 queries (10 ES, 10 EN, 5 typos/jerga, 5 ambiguas/fuera de dominio)
**KB observada:** 52 chunks estructurales por sección H2
**Costo total del experimento:** USD 0.00283

## 1. Breakdown real de latencia por etapa

El embed de la query pesa mucho más en el total de lo que suponíamos al escribir la Spec.

| Etapa | p50 | p95 | min | max |
|---|---|---|---|---|
| `embed_query` (Vertex) | 243 ms | **662 ms** | 153 ms | 697 ms |
| `retrieve_dense` (memoria) | 1 ms | 3 ms | 1 ms | 5 ms |
| `generate_response` (Gemini) | 815 ms | 1.350 ms | 422 ms | 1.907 ms |
| `send_response` (total) | 1.023 ms | 1.747 ms | 681 ms | 2.182 ms |

**Implicación operativa.** El cache hit ahorra tanto el embed como la generación. La ganancia real de latencia por cache hit es mayor a la que asumíamos. Un hit debería costar < 50 ms (KV read + hash + serialize) contra los ~1.750 ms del path completo — reducción ~35×.

**Implicación para el schema.** El campo `latency_embed_ms` es más informativo de lo que parecía. Se mantiene como campo separado y se agrega alerta si p95 sube encima de 800 ms (indica problema con Vertex regional).

## 2. Chunks huérfanos — el 25% de la KB no aparece nunca en top-3

De los 52 chunks de la KB actual, solo 39 aparecen alguna vez en el top-3 fusionado del corpus de discovery. Los **13 chunks huérfanos** son:

```
billing-plans::enterprise
billing-plans::growth
billing-plans::starter
connectors-connect-hubspot::what-happens-next
connectors-reauthorize-expired::how-to-reconnect
connectors-roadmap::how-to-add-a-connector-you-are-entitled-to
connectors-roadmap::included-on-every-plan
connectors-roadmap::paid-add-on-connectors
dashboards-build::prerequisites
reports-not-arriving::2.-check-your-spam/promotions-folder
reports-not-arriving::4.-check-data-freshness
security-privacy::data-in-transit-&-at-rest
security-privacy::isolation-&-access-control
```

**Explicaciones plausibles y no excluyentes.**

- **Sesgo del corpus de discovery.** 30 queries pueden no cubrir todos los temas (planes de precios, seguridad, etc). Amplificar el corpus antes de sacar conclusión definitiva.
- **Embeddings genéricos.** Chunks como `security-privacy::data-in-transit-&-at-rest` tienen texto muy técnico corto que ninguna query natural del usuario activa. Requieren re-chunkeo con más contexto embebido.
- **Sub-cobertura del vocabulario del usuario.** El usuario pregunta "cuánto cuesta" pero el chunk dice "Starter plan features". El puente semántico existe pero es lejano.

**Acciones sugeridas.**

- **Métrica de vigilancia nueva** (candidata para ADR-0004 o POL-11): `kb_coverage_pct` — porcentaje de chunks vistos en top-K sobre una ventana móvil de 7 días de tráfico real. Umbral inicial: < 60% durante 30 días dispara revisión de chunks huérfanos.
- **Bloqueo blando para POL-11 (KB expansion).** Antes de crecer a 60-100 docs, entender por qué 25% de la KB actual es invisible. Expandir sin diagnosticar amplifica el problema.

## 3. Chunk imán — un chunk domina las queries ambiguas

`dashboards-not-loading::1.-check-your-internet-connection` aparece **4 veces como top-1** en el corpus de 30, un 13% del total. Todas las apariciones son en queries genéricas o ambiguas:

- `amb-03` "no me funciona"
- `amb-04` "help"
- `es-02` "por qué mi dashboard aparece en blanco"
- `amb-01` (parcialmente relacionado, aunque top-1 fue otro chunk)

El texto del chunk (*"Check your internet connection. If other Polaris features are working normally too, this might not be the issue…"*) es lo suficientemente genérico para colar como respuesta a casi cualquier problema de dashboard. El retriever lo prefiere ante queries sin contexto claro.

**Riesgo.** El sistema sesga las respuestas hacia "verifica tu internet" incluso cuando la query no tiene nada que ver. Un usuario que pregunta "help" recibe instrucciones sobre conexión de internet — no útil, no honesto.

**Acciones sugeridas.**

- **Métrica de vigilancia nueva** (candidata para ADR-0005): `chunk_dominance_ratio` — porcentaje de queries donde el chunk más dominante aparece como top-1. Umbral inicial: > 10% durante 30 días dispara revisión. Si un chunk único cubre 20-40% de las queries, hay que fragmentarlo o hacerlo más específico.
- **Corto plazo:** re-chunkear `dashboards-not-loading` para dividir el troubleshooting genérico del troubleshooting específico. O agregar contexto al chunk que reduzca su superposición semántica con queries fuera de contexto.

## 4. Umbral empírico de confianza en `top1_score`

Distribución del score del chunk top-1 sobre las 30 queries:

```
0.9+   :                  (0)
0.8-0.9:  ####            (4)   queries tipicas
0.7-0.8:  ##########      (10)  queries tipicas
0.6-0.7:  ###########     (11)  queries tipicas
0.5-0.6:  #               (1)   query tipica limite
0.4-0.5:  ##              (2)   queries fuera de dominio o ambiguas
<0.4   :  ##              (2)   queries claramente fuera de dominio
```

**Hallazgo clave.** Todas las queries con `top1_score < 0.5` son fuera de dominio o ambiguas cortas. Es un umbral empírico natural que no habíamos derivado, solo intuido.

**Aplicación directa en el sistema.**

- **Trigger para forzar "no sé" honesto.** Si `top1_score < 0.50`, el prompt del sistema puede recibir instrucción reforzada para responder "no tengo información sobre esto" incluso si los chunks se ven parcialmente relacionados. Elimina el chunk imán descrito arriba.
- **Trigger para v2.1 clarify multi-turn.** Si `top1_score` está en 0.4-0.6 y el patrón "query corta" aparece, es candidato para pedir clarificación al usuario. La decisión de meter multi-turn tiene ahora un criterio de activación empírico, no una idea especulativa.

## 5. Bug real detectado: idioma de respuesta cambia cuando el LLM dice "no sé"

**Query `es-06`:** *"la alerta que configuré ayer no llegó al Slack"* (español).
**Respuesta observada:** *"The excerpts do not contain information about integrating with Slack for alert notifications."* (inglés).

El prompt del sistema está en inglés y las instrucciones al LLM sobre el idioma son implícitas. Cuando el LLM responde afirmativamente cita evidencia y tiende a responder en el idioma del query. Cuando responde "no sé", **cae al idioma del prompt del sistema — inglés**.

**Impacto.** Usuario hispanohablante que pregunta en español y recibe una respuesta en inglés diciendo "no puedo ayudarte" percibe el sistema como roto. Además contradice el compromiso multilingual (Principio XIV).

**Acción sugerida.**

- **Validación empírica de POL-9.** Este bug es exactamente lo que POL-9 (Multilingual explícito) resuelve. El prompt de v2 debe forzar `respond in the same language as the customer question, including refusals and clarifications`. No un implícito, un explícito.
- Agregar caso a la eval framework de POL-10: query en cualquier idioma sobre tema fuera de KB → respuesta en el idioma del query.

## 6. Unit economics actualizada

**Media empírica:** ~11.136 respuestas por USD 1 con `gemini-2.5-flash-lite` (mediana de costo por respuesta: USD 0.000084).

**Comparación con la unit economics del README público** (~5.500 por USD 1): la nueva medida es **2× mejor**. Es dato para actualizar el README con evidencia empírica del corpus real y la KB de 52 chunks.

## 7. Ajustes concretos derivados para el schema BQ

Los siguientes cambios en el schema draft de `plan.md` sección 3 se derivan de este discovery:

| Campo original | Cambio propuesto | Justificación |
|---|---|---|
| `kb_section` | Renombrar a `top1_source` (nombre del `.md`) + `top1_heading` (heading H2) | El discriminador real es `source::heading`, no una sección abstracta. |
| `intent_predicted` + `intent_confidence` | Marcar nullable con nota "solo se llenan cuando POL-6 canonicalize + clasificación se activen". v1 no clasifica intents explícitos. | El Worker actual no produce este dato — inventarlo genera falsa señal. |
| `grounded_answer` (boolean) | Cambiar a `answer_type` enum: `grounded`, `no_evidence`, `refused_out_of_domain` | La heurística binaria falló en 1/30 casos. Un enum captura mejor la variedad real observada. |
| `top1_score` | Documentar umbral empírico: < 0.50 = confianza baja → trigger honesto. | Umbral empírico derivado de la distribución observada. |
| — nuevo — | `kb_coverage_pct` | Métrica derivada agregable a nivel de dashboard, no de evento. |
| — nuevo — | `chunk_dominance_top1_ratio` | Métrica derivada agregable a nivel de dashboard. |

Los dos campos nuevos son métricas agregadas, no columnas del evento. Se calculan con SQL sobre la tabla `events` en Grafana y se muestran como widgets del dashboard.

## 8. Formato XES-lite — habilitación de process mining futuro

Los traces se guardaron en `traces.jsonl` con 180 eventos (30 casos × 6 actividades). El formato es compatible con `PM4Py` sin conversión adicional:

```python
import pandas as pd
import pm4py
df = pd.read_json("traces.jsonl", lines=True)
df["time:timestamp"] = pd.to_datetime(df["timestamp"])
df["case:concept:name"] = df["case_id"]
df["concept:name"] = df["activity"]
event_log = pm4py.format_dataframe(df)
```

Esto habilita — cuando el hobbie de process mining se retome — discovery de proceso, conformance checking del flow real vs declarado, y análisis de performance por actividad. No es sustancia de v2; es habilitación gratis por elegir el formato correcto en el discovery.
