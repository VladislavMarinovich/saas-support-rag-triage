"""Exporta los chunks de la KB + sus vectores → JSON bundled en el Worker.

El Worker de la vista en vivo hace cosine contra estos vectores en JS (sin vector DB,
ver ADR 0001): `worker/index.js` importa `./kb_vectors.json` en build time, así que
**este archivo ES el índice denso de producción** — el Worker no consulta Mongo en
runtime. Los vectores son Vertex `text-embedding-005` (768d); la query en vivo se
embebe con el MISMO modelo, así el espacio coincide y NO hay que re-indexar.

Dos rutas para generarlo:

    python -m src.export_kb_vectors              # desde Mongo (system-of-record, ADR 0001)
    python -m src.export_kb_vectors --from-kb    # desde kb/ directo: chunk + embed, sin Mongo

La ruta `--from-kb` existe porque el índice del Worker no depende de Mongo para nada:
cuando el cluster no está disponible (POL-11 subtarea 11.4: Atlas rechazando el TLS
handshake) el bundle se puede regenerar igual, sin bloquear el deploy. El precio es que
Mongo queda desincronizado hasta que se corra `python -m src.vectorstore`; eso se
registra en la bitácora y no afecta el runtime.

Ambas rutas producen el MISMO formato — `[{chunk_id, text, vector}]` con el vector
redondeado a 6 decimales — porque es lo que `worker/index.js` consume (línea 123).
"""

from __future__ import annotations

import argparse
import json
import os

OUT = "worker/kb_vectors.json"
DECIMALES = 6  # imperceptible para cosine y baja ~40% el peso del bundle


def _escribir(docs: list[dict], out: str) -> int:
    for d in docs:
        d["vector"] = [round(x, DECIMALES) for x in d["vector"]]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(docs, fh, ensure_ascii=False)  # compacto: es data, no para leer a mano
    return len(docs)


def export(out: str = OUT) -> int:
    """Exporta desde Mongo (`polaris.kb_chunks`), el system-of-record del ADR 0001."""
    from src.mongo_store import get_db

    db = get_db()
    docs = list(db.kb_chunks.find({}, {"_id": 0, "chunk_id": 1, "text": 1, "vector": 1}))
    if not docs:
        raise SystemExit("polaris.kb_chunks vacía — corre `python -m src.vectorstore` primero.")
    return _escribir(docs, out)


def export_desde_kb(out: str = OUT) -> int:
    """Chunkea y embebe `kb/` en el momento, sin pasar por Mongo.

    Usa el MISMO chunker (`src/chunk_kb.py`) y el MISMO modelo (`src/embed.py`) que la
    ruta de Mongo — el scope freeze de v2 (kb-expansion.md §2) los deja intocados.
    """
    from src.chunk_kb import chunk_kb
    from src.embed import embed_texts

    chunks = chunk_kb()
    vectores = embed_texts([c.text for c in chunks])
    docs = [
        {"chunk_id": c.chunk_id, "text": c.text, "vector": [float(x) for x in v]}
        for c, v in zip(chunks, vectores)
    ]
    return _escribir(docs, out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera el índice denso bundled del Worker")
    parser.add_argument(
        "--from-kb",
        action="store_true",
        help="chunkea y embebe kb/ directo, sin leer de Mongo",
    )
    parser.add_argument("--out", default=OUT)
    args = parser.parse_args()

    n = export_desde_kb(args.out) if args.from_kb else export(args.out)
    kb = round(os.path.getsize(args.out) / 1024)
    fuente = "kb/ (chunk + embed)" if args.from_kb else "Mongo"
    print(f"exportados {n} chunks+vectores desde {fuente} → {args.out} ({kb} KB)")
