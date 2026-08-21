<!-- Spec de feature — POL-11 subtarea 11.2 (docs-first). Define QUÉ artículos se escriben en 11.3 y con qué reglas. El checklist anti-huérfano vive en specs/001-polaris-v2/kb-audit.md §4 (derivado de evidencia empírica en 11.1) y es normativo: este documento no lo repite, lo referencia. -->

# KB expansion — especificación

**Historia:** POL-11 · **Subtarea:** 11.2
**Refs:** Spec §3 (Expansión de KB) y §4 (criterio de no-dilución), Spec §5 (scope freeze), Plan §4 Fase 2, [kb-audit.md](../../specs/001-polaris-v2/kb-audit.md) (11.1), [polaris-producto.md](../producto/polaris-producto.md) (nomenclatura), [eval.md](eval.md) (instrumento), Constitution Principios V, XII, XIII, XIV.

## 1. Objetivo y tamaño

La KB pasa de **20 artículos** a **75** (20 existentes + 55 nuevos), dentro del rango 60-100 comprometido en el Plan. El criterio de éxito no es el conteo: es que **preguntas antes fuera de cobertura tengan respuesta grounded sin degradar las que ya funcionaban** (Spec §4, regla de no-regresión eval.md §7).

Reparto de los 55 nuevos:

| Bloque | Artículos | Por qué |
|---|---|---|
| **Catálogo de códigos de error** | 40 | Cobertura de soporte real + es el caso canónico donde BM25 supera al denso (POL-7). |
| **Módulos sin cobertura** | 15 | El baseline mostró huecos temáticos: Editar, Agente LLM, escalamiento a staff, detalle de planes/conectores. |

## 2. Estructura intocable (scope freeze)

No se toca en v2, por Spec §5: **modelo de embeddings** (`text-embedding-005`), **estrategia de chunking** (H2 self-contained, sin overlap), **pipeline** (`src/chunk_kb.py`). Los artículos nuevos se adaptan a la estructura vigente, nunca al revés.

Formato de cada artículo: `# Título` + intro breve + secciones `## ` autocontenidas. El texto de cierre de soporte va como prosa final del último bloque, **nunca como `## Still stuck?`** (regla 9 del checklist: eso produjo 2 chunks basura que contaminaron el 23% de las queries).

## 3. Bloque A — Catálogo de códigos de error (40 artículos)

Un artículo **por código**, no por familia: el código aparece en el nombre del archivo, en el título y en cada heading, así el `chunk_id` lo contiene y el retrieval léxico (POL-7) lo clava.

**Plantilla obligatoria** (ejemplo canónico, `kb/er005-not-synced-google-ads.md`):

```markdown
# ER005 — Not synced with Google Ads

Polaris shows ER005 when your Google Ads connection stops returning data...

## What ER005 means
(síntoma observable + qué NO es; incluye el token `ER005` otra vez en el cuerpo)

## How to fix ER005 in Google Ads
(pasos concretos; termina con el cierre de soporte como prosa)
```

Headings con el código y su tema — nunca `## Symptom` / `## Fix` sueltos (regla 1).

**Reparto por familia** (nomenclatura de `polaris-producto.md`; los códigos concretos los define 11.3 respetando los ya comprometidos en el corpus de eval — **ER005, PF003, RP001 son obligatorios**, ya existen como queries `ec-01/02/03`):

| Familia | Dominio | Artículos |
|---|---|---|
| **ER** | Conexión y sincronización de conectores | 10 |
| **PF** | Permisos y accesos | 6 |
| **PL** | Límites de plan y facturación | 5 |
| **RP** | Envío de reportes | 6 |
| **AL** | Alertas | 4 |
| **DB** | Dashboards y frescura de datos | 5 |
| **AG** | Agente LLM del producto | 4 |

## 4. Bloque B — Módulos sin cobertura (15 artículos)

Derivado de los huecos que el baseline y el audit expusieron, no de intuición:

| Tema | Artículos | Evidencia del hueco |
|---|---|---|
| **Editar** (modificar dashboards; frecuencia y destinatarios de reportes) | 3 | Módulo declarado en `polaris-producto.md` sin ningún artículo. |
| **Agente LLM** (qué responde, qué no, cómo citar fuentes) | 2 | Ídem. Además el producto ES el demo — un reviewer va a preguntar. |
| **Escalamiento a staff** | 2 | Directiva de Vlad: hay routing a área para casos que solo staff resuelve. El schema ya tiene `route: escalate_human`; la KB debe decir **cuándo** aplica (ej. disputas de facturación, borrado de cuenta) para que el bot no intente responder. |
| **Planes y conectores en detalle** (qué conector en qué plan, límites de conexiones) | 4 | 3 de los 13 huérfanos eran chunks de pricing; `paid-add-on-connectors` sigue huérfano incluso con query dirigida — necesita un artículo por conector, no una lista en prosa (regla 4). |
| **Permisos por rol y seguridad** | 2 | `security-privacy::isolation-&-access-control` huérfano; `users-permission-denied::Role reference` invisible al eval. |
| **Atribución y UTMs (casos prácticos)** | 2 | 2 huérfanos de atribución por lenguaje demasiado abstracto. |

**Regla para los 4 de conectores:** un artículo por conector nombrándolo en el título (`Connect Salesforce`, `Connect Meta Ads`…), con el plan requerido explícito. Corrige la causa raíz del huérfano más duro del audit.

## 5. Trazabilidad al corpus de eval (obligatoria)

Por el checklist (reglas 10 y 12), **ningún artículo se acepta sin su query**:

- Cada artículo nuevo aporta ≥1 query al corpus, escrita con vocabulario de usuario y **no** copiada del artículo (copiar mide eco, no retrieval).
- Las nuevas queries se marcan `post_baseline: true` y `source: "pol11"` — y esto **exige implementar la sección aparte de `post_baseline`** en el reporte (deuda menor #1 de la auditoría 10.5): hasta hoy el runner solo tiene un guard fail-fast. **Es prerrequisito de 11.5.**
- Las 3 queries de códigos ya existentes (`ec-01/02/03`) se **re-etiquetan** de `fuera_de_dominio` a `grounded` apuntando a sus artículos nuevos. Ese cambio de etiqueta es la medición de que la expansión sirvió.
- Se agrega la categoría **`staff_only`** con `expected_route: escalate_human` para los artículos de escalamiento: "no sé" y "esto lo ve un humano" son resultados distintos y se miden distinto.

## 6. Orden de ejecución dentro de POL-11

El GO de Vlad (21-ago) al **saneamiento del índice** cambia el orden interno de la Historia:

1. **11.3** — redactar los 55 artículos (este spec).
2. **11.4** — re-chunk + re-embed + **saneamiento del índice del eval**: unificar con el criterio de producción (strippear el footer del texto crudo antes de segmentar) para recuperar las 18 secciones perdidas y eliminar los 2 chunks basura (kb-audit §3).
3. **11.5** — re-correr el eval y **re-estampar el baseline**: el saneamiento + la KB nueva hacen que el baseline v1 publicado quede medido sobre un índice que ya no existe. `baseline.md` se re-publica declarando explícitamente ambos cambios (índice saneado + KB expandida) y conservando la corrida original como referencia histórica. Sin esto, los deltas de v2 comparan contra un instrumento defectuoso.

**Consecuencia aceptada:** el gate se re-estampa una vez. Es preferible a arrastrar un asterisco permanente en la tabla comparativa de v2.

## 7. Criterio de aceptación de la Historia

- 75 artículos totales, los 55 nuevos cumpliendo el checklist de kb-audit §4 (verificable artículo por artículo).
- `kb_coverage_pct` orgánico ≥ 96% sobre el corpus ampliado; ningún chunk nuevo supera 10% de dominancia top-1.
- Recall@5 y MRR sin degradación en las queries donde v1 acertaba (eval.md §7).
- `ec-01/02/03` pasan de `no_evidence` a `grounded` — la prueba medible de que la expansión funcionó.
- Ningún artículo nuevo nace huérfano (regla 12: si su chunk no aparece en top-5 de su propia query, se reescribe).

## 8. Fuera de alcance

Re-chunking con estrategia distinta · cambio de modelo de embeddings · traducción de la KB a otros idiomas (la KB queda en inglés técnico; el LLM traduce en generación — Principio XIV) · artículos de features que no existen en `polaris-producto.md` (no inventar producto durante la redacción).
