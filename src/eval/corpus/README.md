# Corpus etiquetado — eval framework (POL-10, subtarea 10.2)

**Instrumento de medición.** Cambiar este corpus exige PR ([eval.md §2](../../../docs/features/eval.md)) — cambiarlo silenciosamente invalida toda comparación contra el baseline.

- **47 queries** (`corpus.jsonl`): 30 semilla del discovery (`source: "discovery"`) + 17 manuales (`source: "manual"`).
- **KB de referencia:** los 52 chunks vigentes al baseline, chunk_id = `source::heading` en minúsculas con espacios→guiones (el chunker del discovery, `scripts/discovery/observe_flow.py::load_kb_chunks` — NO el de `src/chunk_kb.py`, que produce otra numeración).
- **Cobertura:** 29 típicas · 7 typo/jerga · 4 ambiguas · 7 fuera_de_dominio (3 de ellas con códigos de error ER005/PF003/RP001 — sus artículos no existen hasta POL-11; se re-etiquetan al cerrar POL-11 y la mejora queda medida).

## Reglas de etiquetado

1. **`expected_chunks` es juicio humano contra el texto de `kb/`**, no el top-K observado en discovery: la etiqueta es "qué chunk(s) aceptaría un humano como respuesta correcta". Los traces del discovery se usaron solo como contraste.
2. **`fuera_de_dominio` ⇒ `expected_chunks: []`** y se evalúa por `expected_answer_type` (umbral `top1_score < 0.50`, hallazgo §4 del discovery). Quedan EXCLUIDAS de Recall/Precision/MRR.
3. **Ambiguas:** pueden llevar chunks (si la KB cubre la interpretación dominante, ej. `man-12` "no llegan los correos" → reports-not-arriving) o lista vacía + `no_evidence` (si ninguna respuesta es defendible sin clarificar, ej. `amb-03` "no me funciona", `amb-04` "help"). Las de lista vacía también quedan excluidas de Recall/Precision/MRR (no hay chunk correcto que recuperar) y se reportan junto a las fuera_de_dominio en el chequeo de answer_type.
4. **`no_evidence` vs `refused_out_of_domain`:** `no_evidence` = pregunta del producto que la KB actual no cubre (códigos de error, WhatsApp); `refused_out_of_domain` = fuera del producto (vuelos, Bitcoin, planes de marketing).

## Decisiones de etiquetado no obvias

| Query | Decisión |
|---|---|
| `es-02`/`en-02` (dashboard en blanco) | Se EXCLUYE `dashboards-not-loading::1.-check-your-internet-connection` ("recarga la página" no responde el porqué); es el chunk imán del hallazgo §3 del discovery — etiquetarlo como correcto premiaría el sesgo. Valen los pasos 2/3/4. |
| `es-06`/`en-10` (alerta no llegó) | La KB no cubre Slack; el artículo `alerts-not-firing` sí resuelve la necesidad de fondo (por qué no llegó la alerta) → sus 3 chunks vigentes son respuesta aceptable, `grounded`. |
| `amb-02` (TikTok Ads) | **Re-etiquetada** respecto al discovery (era fuera de dominio): la KB vigente SÍ la responde (`connectors-roadmap::paid-add-on-connectors`, actualizado post-discovery). v1 denso no lo recuperó en top-3 — candidata a delta de BM25 (POL-7) por término exacto "TikTok". |
| `typo-04` (api key rotation) | Polaris usa OAuth, no API keys; la tarea equivalente es reconectar → `how-to-reconnect` + `connector-security`. |
| `man-09` (SSO en Growth) | SSO es Enterprise-only → `billing-plans::enterprise` responde; además es chunk huérfano del hallazgo §2 (a propósito: mide si el denso lo encuentra). |
| `man-02`..`man-05` | Apuntan deliberadamente a chunks huérfanos del hallazgo §2 (billing-plans, security-privacy, connectors-roadmap) para que la KB invisible quede medida en el baseline. |
| `ec-01`..`ec-03` (códigos de error) | Directiva de Vlad (bitácora 21-ago): `fuera_de_dominio` + `expected_chunks: []` contra la KB actual; `no_evidence` (pregunta de producto sin artículo aún). Se re-etiquetan al cerrar POL-11. |

## Validación

```bash
uv run python -m src.eval.validate_corpus
```

Verifica: schema completo por línea, ids únicos, categorías/answer_types dentro del enum, y que cada `expected_chunk` exista en los 52 chunk_ids vigentes de `kb/`.
