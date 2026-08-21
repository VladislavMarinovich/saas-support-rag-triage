# src/eval — eval framework de retrieval (POL-10)

Medidor determinista de retrieval: corre el corpus etiquetado contra una config
del sistema y reporta métricas de recuperación, latencia y costo. **La fuente de
verdad es [docs/features/eval.md](../../docs/features/eval.md)** — este código la
implementa; si divergen, gana el documento o se actualiza vía PR.

## Correr el eval (un solo comando)

```bash
uv run python -m src.eval.run --config v1
```

Opciones: `--top-k 5` (default) · `--out reporte.md` (además de stdout) ·
`--fecha 2026-08-21` (inyectable para reproducir el reporte byte a byte).
`--config v2` existe como hook y falla con mensaje claro hasta POL-7.

Requisitos: ADC de Google activo (`gcloud auth application-default login`) SOLO
para el primer run — después los embeddings salen del cache y el run cuesta USD 0.

## Piezas

| Archivo | Qué hace |
|---|---|
| `run.py` | CLI: orquesta corpus → embeddings → cosine → métricas → reporte |
| `metrics.py` | Recall@1/@5, Precision@5, MRR, percentiles, answer_type — funciones puras |
| `report.py` | Render Markdown pegable en PR (formato eval.md §6) |
| `kb_index.py` | Chunking de la KB (réplica exacta del chunker del discovery, 52 chunks `source::heading`) |
| `embed_cache.py` | Cache de embeddings en `cache/` (gitignoreado) — determinismo + segundo run gratis |
| `corpus/` | Corpus etiquetado (47 queries) + reglas de etiquetado — instrumento de medición, cambiar exige PR |
| `validate_corpus.py` | Valida schema del corpus y que cada etiqueta exista en la KB |
| `test_metrics.py` | Tests con casos calculados a mano — la evidencia de que el medidor mide bien |

## Verificar

```bash
uv run python -m src.eval.test_metrics      # tests de métricas (sin red, sin costo)
uv run python -m src.eval.validate_corpus   # integridad del corpus vs KB vigente
```

## Decisiones de implementación (registradas en bitácora 21-ago)

- **Índice del eval = chunker del discovery** (52 chunks, ids `source::heading`), NO
  `src/chunk_kb.py` (90 chunks, `stem#i`): el corpus está etiquetado en ese esquema.
  La divergencia con el Worker JS está registrada en `bitacora/hallazgos.md` y la
  resuelve POL-7 antes del test de paridad (`eval.md` §4).
- **Cosine**: la misma matemática de `src/vectorstore.py::search` (normalizar + dot,
  argsort estable) sin el acople a Mongo; embeddings vía `src/embed.py` (mismo modelo
  y endpoint que producción).
- **Latencia reportada = embed de la query** (congelada en cache en el primer run):
  el cosine in-memory agrega ~1-3 ms (discovery §1) y varía por run, así que se
  imprime en consola y no entra al reporte — el reporte es 100% determinista.
- **Queries sin chunk esperado** (fuera de dominio y ambiguas irrescatables) quedan
  fuera de Recall/Precision/MRR y se evalúan por answer_type (umbral `top1_score < 0.50`).
