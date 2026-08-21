"""Cobertura de la KB — `kb_coverage_pct`, huérfanos, imanes y secciones sin indexar.

Instrumento de la auditoría 11.1 (`specs/001-polaris-v2/kb-audit.md`), dejado
reproducible porque 11.5 debe recalcular `kb_coverage_pct` sobre la KB expandida
y compararla contra el número de esta auditoría — y porque ADR-0004/0005 definen
la cobertura y la dominancia como métricas de vigilancia permanentes.

Reutiliza el retrieval del eval (config v1, cache caliente ⇒ USD 0). NO construye
ni modifica el índice: solo lo mide.

    uv run python -m src.eval.coverage
    uv run python -m src.eval.coverage --corpus-subset organico --top-k 5
"""

from __future__ import annotations

import argparse
import re
from collections import Counter

import numpy as np

from src.eval.embed_cache import get_embedding, get_embeddings_batch
from src.eval.kb_index import KB_DIR, kb_index_hash, load_kb_chunks
from src.eval.run import _normalizar, cargar_corpus

# queries escritas en 10.2 apuntando DELIBERADAMENTE a chunks huérfanos: la
# cobertura que ellas aportan no es evidencia de salud de la KB (sería circular),
# así que el subconjunto "organico" las excluye. Ver kb-audit.md §1.
QUERIES_DIRIGIDAS = {"man-02", "man-03", "man-04", "man-05", "man-09", "amb-02"}

# umbrales de vigilancia (ADR-0004 cobertura, ADR-0005 dominancia)
UMBRAL_COBERTURA_PCT = 60.0
UMBRAL_DOMINANCIA_PCT = 10.0


def rankings(corpus: list[dict], top_k: int) -> tuple[list[str], dict[str, list[str]]]:
    """Devuelve (ids del índice, {query_id: ranking de top_k chunk_ids})."""
    kb = load_kb_chunks()
    ids = [c["chunk_id"] for c in kb]
    entradas = get_embeddings_batch([c["text"] for c in kb])
    mat = _normalizar(np.asarray([e["vector"] for e in entradas], dtype=np.float32))

    por_query: dict[str, list[str]] = {}
    for fila in corpus:
        qv = _normalizar(np.asarray([get_embedding(fila["query"])["vector"]], dtype=np.float32))[0]
        scores = mat @ qv
        orden = np.argsort(-scores, kind="stable")[:top_k]
        por_query[fila["id"]] = [ids[i] for i in orden]
    return ids, por_query


def cobertura(ids: list[str], por_query: dict[str, list[str]]) -> tuple[float, list[str]]:
    """kb_coverage_pct y lista de huérfanos (chunks nunca vistos en el top-K)."""
    vistos = {cid for ranking in por_query.values() for cid in ranking}
    huerfanos = [c for c in ids if c not in vistos]
    return (len(ids) - len(huerfanos)) / len(ids) * 100, huerfanos


def dominancia(por_query: dict[str, list[str]]) -> list[tuple[str, int, float]]:
    """Chunks más frecuentes como top-1: (chunk_id, veces, % del corpus)."""
    top1 = Counter(r[0] for r in por_query.values() if r)
    n = len(por_query)
    return [(cid, veces, veces / n * 100) for cid, veces in top1.most_common()]


def secciones_sin_indexar() -> list[tuple[str, str, int]]:
    """Secciones H2 de kb/ que NO existen como chunk del índice: (source, heading, chars).

    Dimensiona la pérdida del filtro de boilerplate del chunker (kb-audit.md §3).
    """
    indexadas = {(c["source"], c["heading"]) for c in load_kb_chunks()}
    faltantes: list[tuple[str, str, int]] = []
    for md in sorted(KB_DIR.glob("*.md")):
        texto = md.read_text(encoding="utf-8")
        for heading in re.findall(r"^## +(.+)$", texto, flags=re.M):
            heading = heading.strip()
            if (md.stem, heading) in indexadas:
                continue
            cuerpo = re.search(
                rf"^## +{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", texto, flags=re.M | re.S
            )
            # medir el cuerpo SIN el footer boilerplate: es el contenido que se pierde
            util = re.split(r"\n-{3,}\s*\n|\*\*Still stuck", (cuerpo.group(1) if cuerpo else ""))[0]
            faltantes.append((md.stem, heading, len(util.strip())))
    return faltantes


def main() -> None:
    parser = argparse.ArgumentParser(description="Cobertura de la KB (POL-11 · 11.1)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--corpus-subset",
        choices=["completo", "organico", "discovery", "manual"],
        default="completo",
        help="'organico' excluye las queries escritas para cubrir huérfanos (medida honesta)",
    )
    args = parser.parse_args()

    corpus = cargar_corpus()
    if args.corpus_subset == "organico":
        corpus = [f for f in corpus if f["id"] not in QUERIES_DIRIGIDAS]
    elif args.corpus_subset in ("discovery", "manual"):
        corpus = [f for f in corpus if f["source"] == args.corpus_subset]

    kb = load_kb_chunks()
    ids, por_query = rankings(corpus, args.top_k)
    pct, huerfanos = cobertura(ids, por_query)

    print(
        f"KB {len(kb)} chunks (hash {kb_index_hash(kb)}) · corpus '{args.corpus_subset}' "
        f"{len(corpus)} queries · top-{args.top_k}"
    )
    print(f"\nkb_coverage_pct = {pct:.1f}%  (umbral de vigilancia: {UMBRAL_COBERTURA_PCT:.0f}%)")
    print(f"huérfanos: {len(huerfanos)}")
    for h in huerfanos:
        print("   ", h)

    print("\nchunk_dominance_top1_ratio (umbral " f"{UMBRAL_DOMINANCIA_PCT:.0f}%):")
    for cid, veces, ratio in dominancia(por_query)[:5]:
        marca = "  ⚠ sobre umbral" if ratio > UMBRAL_DOMINANCIA_PCT else ""
        print(f"   {ratio:5.1f}%  ({veces:2d} veces top-1)  {cid}{marca}")

    faltantes = secciones_sin_indexar()
    print(f"\nsecciones H2 de kb/ SIN chunk en el índice: {len(faltantes)}")
    for source, heading, chars in faltantes:
        print(f"   {source}::{heading}  ({chars} chars de contenido)")
    basura = [c["chunk_id"] for c in kb if "still-stuck" in c["chunk_id"]]
    if basura:
        print(f"\nchunks de puro boilerplate indexados: {len(basura)}")
        for b in basura:
            print("   ", b)


if __name__ == "__main__":
    main()
