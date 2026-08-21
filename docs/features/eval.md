<!-- Spec de feature — POL-10 subtarea 10.1 (docs-first). Fuente de verdad del eval framework. El código de src/eval/ implementa ESTE documento; si divergen, gana este documento o se actualiza vía PR. -->

# Eval framework — especificación

**Historia:** POL-10 (Eval framework + baseline) · **Subtarea:** 10.1
**Refs:** Spec §3 y §4 (criterios), Plan §4 Fases 1 y 8, Constitution Principios IV (costo), V (clásico donde funciona), XII (eval-driven), [tasks.md](../../specs/001-polaris-v2/tasks.md) bloque POL-10.

## 1. Qué es y qué NO es

Un **medidor determinista de retrieval** implementado a mano en Python (`src/eval/`): corre un corpus etiquetado contra una configuración del sistema (v1 dense-only o v2 híbrido) y reporta métricas de recuperación, latencia y costo. Mismo corpus + misma config = mismos números, siempre.

**NO es** un juez LLM (RAGAS/DeepEval descartados: pagan llamadas LLM para juzgar lo que acá se resuelve comparando listas contra etiquetas humanas, con varianza cero y costo cero). La calidad de la *respuesta generada* se valida por otras vías ya definidas: validación manual (9.6) y checks exactos de idioma (9.8).

**NO depende del Worker vivo** (criterio Spec §4): replica el pipeline de retrieval en Python reutilizando los módulos offline existentes (`src/vectorstore.py` para dense; el índice BM25 de POL-7 se construye offline en Python y se exporta a JSON — Plan §5 — así que el eval usa la MISMA construcción del índice que producción).

## 2. Corpus etiquetado

Archivo: `src/eval/corpus/corpus.jsonl` — una query por línea:

```json
{
  "id": "es-06",
  "query": "la alerta que configuré ayer no llegó al Slack",
  "lang": "es",
  "categoria": "tipica | typo_jerga | fuera_de_dominio | ambigua",
  "expected_chunks": ["alerts-not-firing::steps", "alerts-configure::prerequisites"],
  "expected_answer_type": "grounded | no_evidence | refused_out_of_domain",
  "source": "discovery | pol9 | manual",
  "post_baseline": false
}
```

Reglas del corpus:

- **Semilla:** las 30 queries del discovery (ya tienen traces reales). Meta: 30-50 al cerrar 10.2.
- **`expected_chunks`** es la lista de chunk_ids (`source::heading`) que un humano acepta como respuesta correcta — puede haber más de uno válido. Para queries `fuera_de_dominio` la lista es vacía y lo que se evalúa es `expected_answer_type`.
- **Etiquetado contra la KB vigente al momento del baseline** (52 chunks). Cuando POL-11 expanda la KB, las etiquetas se REVISAN (un chunk nuevo puede volverse la mejor respuesta) y el cambio queda en el PR de POL-11.
- **`post_baseline: true`** marca casos agregados después del baseline (p. ej. los de 9.8): entran al reporte en sección aparte y NUNCA se comparan contra un baseline que no los midió.
- El corpus se versiona en git; cambiarlo exige PR (es parte del instrumento de medición — cambiarlo silenciosamente invalida toda comparación).

## 3. Métricas

Sea `E` el conjunto de chunks esperados y `R = [r1, r2, ...]` el ranking recuperado.

| Métrica | Definición | Qué responde |
|---|---|---|
| **Recall@1** | 1 si `r1 ∈ E`, promedio sobre el corpus | ¿el mejor chunk queda de primero? |
| **Recall@5** | 1 si `E ∩ {r1..r5} ≠ ∅`, promedio | ¿la respuesta correcta llega al contexto del LLM? |
| **Precision@5** | `|E ∩ {r1..r5}| / 5`, promedio | ¿cuánto ruido entra al prompt? |
| **MRR** | `1/rank` del primer chunk de `E` en `R` (0 si no aparece), promedio | ¿qué tan arriba aparece lo correcto? |
| **Latencia p50/p95** | percentiles del tiempo de retrieval por query | ¿aporta al SLO p95 < 2s (Principio X)? |
| **Costo promedio** | USD por query del run (solo embeddings; ver cache abajo) | ¿cuánto cuesta medir? (Principio IV) |
| **answer_type match** | solo para `fuera_de_dominio`: ¿el score gatilla el umbral 0.50? | ¿el "no sé" honesto funciona? |

Las queries `fuera_de_dominio` se EXCLUYEN de Recall/Precision/MRR (no tienen chunk correcto) y se reportan aparte por `answer_type match`. Los agregados se reportan también **por idioma** (criterio Spec §6: sin sesgo severo entre idiomas) y **por categoría**.

## 4. Configuraciones comparables

```
python -m src.eval.run --config v1              # dense-only (baseline)
python -m src.eval.run --config v2              # dense + BM25 + RRF k=60
python -m src.eval.run --config v1 --config v2  # tabla comparativa con delta
```

Una config declara: método de retrieval, versión de KB (conteo de chunks + hash del índice), top-K. La config exacta se imprime en el reporte — un número sin su config no es evidencia.

**Paridad JS/Python (regla dura, DIFERIDA a POL-7):** el scoring que el eval usa en Python debe producir el mismo ranking que el Worker en JS. Se garantiza con un set de **5 queries doradas** verificadas en ambos lados (`src/eval/test_parity.py` + test espejo en el Worker). *Estado real (auditoría 10.5, 21-ago):* hoy la paridad es INAPLICABLE — el eval indexa 52 chunks `source::heading` (chunker del discovery, contra el que está etiquetado el corpus) y el Worker consulta 90 chunks `stem#i` (`worker/kb_vectors.json`). POL-7 unifica el chunker ANTES de escribir el test de paridad y de construir BM25; las queries doradas se eligen en ese momento. Hasta entonces, las comparaciones v1 vs v2 valen solo DENTRO del eval (mismo índice), que es lo que el baseline necesita.

## 5. Costo y cache de embeddings

Embeder ~50 queries cuesta ~USD 0.001 (referencia discovery: 30 queries = USD 0.00283 con generación incluida). Aun así, los embeddings de queries se cachean en `src/eval/cache/` (hash del texto → vector, gitignoreado): re-correr el eval en iteración cuesta USD 0. El costo real del run se imprime en el reporte.

## 6. Formato del reporte

Salida en Markdown pegable directo en el PR (política Spec §4: PR sin eval no se mergea):

```markdown
## Eval — 2026-08-XX · corpus v1 (30 queries) · KB 52 chunks (hash abc123)
| Métrica      | v1 (baseline) | v2    | Δ       |
|--------------|---------------|-------|---------|
| Recall@1     | 0.63          | 0.77  | +0.14   |
| Recall@5     | 0.83          | 0.93  | +0.10   |
| Precision@5  | 0.21          | 0.26  | +0.05   |
| MRR          | 0.71          | 0.83  | +0.12   |
| p95 (ms)     | 662           | 684   | +22     |
| Costo/query  | $0.000021     | $0.000021 | =   |
(+ desglose por idioma y por categoría · casos post_baseline aparte · config exacta al pie)
```

*(números ilustrativos — los reales salen de 10.4)*

El baseline oficial se publica en `specs/001-polaris-v2/baseline.md` (subtarea 10.4) y es **el gate** que desbloquea POL-6/7/9/11.

## 7. Regla de no-regresión

Un PR degrada si Recall@5 o MRR caen respecto al baseline en los casos donde v1 acertaba (criterio Spec §4). La magnitud tolerable se congela en 10.8 con datos; hasta entonces, cualquier caída se justifica por escrito en el PR o se rechaza.

## 8. Fuera de alcance de esta spec

Juez LLM para calidad de respuesta (v2.1 si algún día se justifica) · métricas de generación (tokens, grounding — las cubre la telemetría POL-8 en producción) · eval sobre tráfico real (eso es el dashboard).
