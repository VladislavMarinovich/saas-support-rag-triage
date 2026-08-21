"""Validador del corpus etiquetado — POL-10 subtarea 10.2.

Chequea que `corpus.jsonl` cumpla el contrato de eval.md §2: schema completo,
ids únicos, enums válidos, y que cada expected_chunk exista en la KB vigente
(los chunk_ids que produce src/eval/kb_index.py). Un corpus con etiquetas que
apuntan a chunks inexistentes daría Recall=0 falso — mejor reventar acá.

Run:  uv run python -m src.eval.validate_corpus
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from src.eval.kb_index import load_kb_chunks

CORPUS_PATH = Path(__file__).resolve().parent / "corpus" / "corpus.jsonl"

CAMPOS = ["id", "query", "lang", "categoria", "expected_chunks", "expected_answer_type", "source", "post_baseline"]
CATEGORIAS = {"tipica", "typo_jerga", "fuera_de_dominio", "ambigua", "staff_only"}
ANSWER_TYPES = {"grounded", "no_evidence", "refused_out_of_domain"}
SOURCES = {"discovery", "pol9", "manual", "pol11"}
LANGS = {"es", "en"}
# staff_only (kb-expansion.md §5): "no sé" y "esto lo ve un humano" son resultados
# distintos, así que esas queries declaran además la ruta esperada.
ROUTES = {"escalate_human"}


def validar(corpus_path: Path = CORPUS_PATH) -> list[str]:
    """Devuelve la lista de errores (vacía = corpus válido)."""
    errores: list[str] = []
    kb_ids = {c["chunk_id"] for c in load_kb_chunks()}

    filas = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    ids = [f.get("id") for f in filas]
    for dup, n in Counter(ids).items():
        if n > 1:
            errores.append(f"id duplicado: {dup} ({n} veces)")

    for f in filas:
        qid = f.get("id", "<sin id>")
        for campo in CAMPOS:
            if campo not in f:
                errores.append(f"{qid}: falta el campo '{campo}'")
        if f.get("categoria") not in CATEGORIAS:
            errores.append(f"{qid}: categoria inválida {f.get('categoria')!r}")
        if f.get("expected_answer_type") not in ANSWER_TYPES:
            errores.append(f"{qid}: expected_answer_type inválido {f.get('expected_answer_type')!r}")
        if f.get("source") not in SOURCES:
            errores.append(f"{qid}: source inválido {f.get('source')!r}")
        if f.get("lang") not in LANGS:
            errores.append(f"{qid}: lang inválido {f.get('lang')!r}")
        # regla eval.md §2: fuera_de_dominio lleva lista vacía
        if f.get("categoria") == "fuera_de_dominio" and f.get("expected_chunks"):
            errores.append(f"{qid}: fuera_de_dominio debe llevar expected_chunks []")
        # coherencia: quien espera grounded debe tener al menos un chunk etiquetado
        if f.get("expected_answer_type") == "grounded" and not f.get("expected_chunks"):
            errores.append(f"{qid}: grounded sin expected_chunks")
        # staff_only ⇄ expected_route: la categoría exige la ruta y la ruta exige la categoría
        if f.get("categoria") == "staff_only" and f.get("expected_route") not in ROUTES:
            errores.append(f"{qid}: staff_only sin expected_route válido ({f.get('expected_route')!r})")
        if f.get("expected_route") and f.get("categoria") != "staff_only":
            errores.append(f"{qid}: expected_route solo aplica a categoria staff_only")
        for cid in f.get("expected_chunks", []):
            if cid not in kb_ids:
                errores.append(f"{qid}: expected_chunk inexistente en la KB: {cid}")

    return errores


def main() -> None:
    errores = validar()
    filas = [json.loads(l) for l in CORPUS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    por_cat = Counter(f["categoria"] for f in filas)
    por_lang = Counter(f["lang"] for f in filas)
    por_source = Counter(f["source"] for f in filas)
    print(f"corpus: {len(filas)} queries · categorías {dict(por_cat)} · idiomas {dict(por_lang)} · source {dict(por_source)}")
    if errores:
        print(f"\n{len(errores)} ERRORES:")
        for e in errores:
            print(" -", e)
        sys.exit(1)
    print("corpus válido ✔")


if __name__ == "__main__":
    main()
