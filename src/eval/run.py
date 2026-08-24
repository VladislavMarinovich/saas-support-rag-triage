"""Runner del eval — corre el corpus etiquetado contra una config de retrieval.

    uv run python -m src.eval.run --config v1              # dense-only (baseline)
    uv run python -m src.eval.run --config v2              # POL-7 — aún no existe
    uv run python -m src.eval.run --config v1 --out reporte.md

Config v1 = retrieval denso puro: embed de la query con Vertex text-embedding-005
(vía src/embed.py, el mismo módulo que indexa producción) y cosine exacto contra
la KB chunkeada en memoria — la misma matemática de src/vectorstore.py::search
(normalizar + dot product) sin el acople a Mongo, porque el índice del eval debe
ser el mismo `source::heading` contra el que está etiquetado el corpus (hoy 184
chunks tras el saneamiento de 11.4; eran 52 cuando se estampó el baseline v1 —
ver bitacora/hallazgos.md 21-ago sobre la divergencia de chunkers).

Determinismo: los embeddings van a src/eval/cache/ (gitignoreado); a partir del
primer run, vectores, rankings, métricas y latencias reportadas quedan
congelados — correr dos veces produce el mismo reporte byte a byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np

from src.eval import metrics, report
from src.eval.embed_cache import get_embedding, get_embeddings_batch
from src.eval.kb_index import kb_index_hash, load_kb_chunks

CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "corpus.jsonl"


def cargar_corpus(path: Path = CORPUS_PATH) -> list[dict]:
    """Lee el corpus completo. La separación por población la hace `particionar`."""
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def particionar(corpus: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separa el corpus en (baseline, post_baseline) — eval.md §2 y §6.

    Los casos `post_baseline: true` se agregaron DESPUÉS de que el baseline se
    midiera, así que promediarlos con los del baseline mezcla dos poblaciones y
    produce un número que no se puede comparar contra nada: ni contra el baseline
    (que no los midió) ni contra un run futuro (donde la mezcla será otra). Por eso
    van a una sección aparte del reporte, con sus propios agregados.

    Hasta 11.5 esta separación no existía y `cargar_corpus` abortaba fail-fast ante
    el primer caso `post_baseline` (deuda menor #1 de la auditoría 10.5). El guard
    protegía la validez del número; esta función la protege sin frenar el runner.
    """
    baseline = [f for f in corpus if not f.get("post_baseline")]
    post = [f for f in corpus if f.get("post_baseline")]
    return baseline, post


def _normalizar(mat: np.ndarray) -> np.ndarray:
    """Norma 1 por fila para que dot == cosine (idéntico a src/vectorstore.py)."""
    normas = np.linalg.norm(mat, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return mat / normas


def correr_v1(corpus: list[dict], top_k: int) -> tuple[list[dict], dict]:
    """Config v1: dense-only. Devuelve (resultados por query, stats del run)."""
    kb = load_kb_chunks()

    # 1. embeddings de la KB (batch, cacheados)
    entradas_kb = get_embeddings_batch([c["text"] for c in kb])
    ids_kb = [c["chunk_id"] for c in kb]
    mat_kb = _normalizar(np.asarray([e["vector"] for e in entradas_kb], dtype=np.float32))

    # 2. correr cada query: embed (cacheado) + cosine + métricas
    resultados: list[dict] = []
    latencias_score: list[float] = []
    gasto_incremental = 0.0
    hits = 0
    for fila in corpus:
        entrada = get_embedding(fila["query"])
        if entrada["cache_hit"]:
            hits += 1
        else:
            gasto_incremental += entrada["cost_usd"]

        t0 = time.time()
        qv = _normalizar(np.asarray([entrada["vector"]], dtype=np.float32))[0]
        scores = mat_kb @ qv
        # argsort estable: ante empate de score el orden no depende del quicksort
        orden = np.argsort(-scores, kind="stable")[:top_k]
        latencias_score.append((time.time() - t0) * 1000)

        ranking = [ids_kb[i] for i in orden]
        resultado = metrics.evaluar_query(fila, ranking, float(scores[orden[0]]), k=top_k)
        # la latencia viaja con la fila para poder calcular percentiles POR POBLACIÓN
        # (baseline vs post_baseline) sin re-correr el retrieval
        resultado["latencia_embed_ms"] = entrada["latency_ms"]
        resultado["post_baseline"] = bool(fila.get("post_baseline"))
        resultados.append(resultado)

    stats = {
        "kb_chunks": len(kb),
        "kb_hash": kb_index_hash(kb),
        "latencias_score": latencias_score,
        "gasto_incremental": gasto_incremental
        + sum(e["cost_usd"] for e in entradas_kb if not e["cache_hit"]),
        "cache_hits": hits + sum(1 for e in entradas_kb if e["cache_hit"]),
        "costo_kb": sum(e["cost_usd"] for e in entradas_kb),
    }
    return resultados, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Eval de retrieval Polaris (POL-10)")
    parser.add_argument("--config", action="append", choices=["v1", "v2"], required=True,
                        help="configuración a evaluar (repetible para comparar)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fecha", default=date.today().isoformat(),
                        help="fecha del reporte (inyectable para reproducir byte a byte)")
    parser.add_argument("--out", type=Path, default=None, help="archivo de salida del reporte")
    args = parser.parse_args()

    if "v2" in args.config:
        sys.exit(
            "config v2 no implementada: el retrieval híbrido (dense + BM25 + RRF k=60) "
            "llega con POL-7. Hasta entonces solo existe --config v1."
        )

    corpus = cargar_corpus()
    corpus_hash = hashlib.sha256(CORPUS_PATH.read_bytes()).hexdigest()[:12]
    corpus_baseline, corpus_post = particionar(corpus)

    resultados, stats = correr_v1(corpus, args.top_k)

    def _agregar_poblacion(filas_corpus: list[dict], es_post: bool) -> dict | None:
        """Agrega UNA población. Devuelve None si la población está vacía."""
        if not filas_corpus:
            return None
        filas = [r for r in resultados if r["post_baseline"] is es_post]
        costo = sum((max(1, len(f["query"]) // 4) / 1000) * 0.000025 for f in filas_corpus)
        agg = metrics.agregar(
            filas,
            latencias_ms=[r["latencia_embed_ms"] for r in filas],
            costo_por_query=costo / len(filas_corpus),
            k=args.top_k,
        )
        agg["costo_total_usd"] = costo
        return agg

    agregados = _agregar_poblacion(corpus_baseline, es_post=False)
    agregados_post = _agregar_poblacion(corpus_post, es_post=True)
    if agregados is None:
        sys.exit("el corpus no tiene ninguna query del baseline: no hay contra qué comparar")

    costo_queries = agregados["costo_total_usd"] + (
        agregados_post["costo_total_usd"] if agregados_post else 0.0
    )

    config = {
        "nombre": "v1 (dense-only)",
        "descripcion": "embed Vertex + cosine exacto in-memory, sin BM25 ni RRF",
        "kb_chunks": stats["kb_chunks"],
        "kb_hash": stats["kb_hash"],
        "corpus_version": (
            f"{len(corpus_baseline)} del baseline + {len(corpus_post)} post_baseline"
        ),
        "corpus_hash": corpus_hash,
        "embed_model": "text-embedding-005",
        "top_k": args.top_k,
        "costo_total_usd": costo_queries + stats["costo_kb"],
    }

    salida = report.render(config, agregados, args.fecha, agregados_post=agregados_post)
    print(salida)
    if args.out:
        args.out.write_text(salida, encoding="utf-8")

    # diagnóstico del run (NO entra al reporte: varía entre runs por diseño)
    print(
        f"[run] cache hits: {stats['cache_hits']} · gasto incremental de este run: "
        f"${stats['gasto_incremental']:.5f} · cosine in-memory p95: "
        f"{metrics.percentil(stats['latencias_score'], 95):.1f} ms",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
