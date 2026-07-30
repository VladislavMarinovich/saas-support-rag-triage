"""Exporta los 89 chunks de la KB + sus vectores → JSON bundled en el Worker.

El Worker de la vista en vivo (fase 2) hace cosine contra estos vectores en JS
(sin vector DB, ver ADR 0001). Los vectores son Vertex `text-embedding-005` (768d);
la query en vivo se embebe con el MISMO modelo, así el espacio coincide y NO hay que
re-indexar. Mongo (`polaris.kb_chunks`) sigue siendo el system-of-record; esto es
una foto para bundlear en el Worker.

Run:  python -m src.export_kb_vectors   # -> worker/kb_vectors.json
"""

from __future__ import annotations

import json
import os

from src.mongo_store import get_db

OUT = "worker/kb_vectors.json"


def export(out: str = OUT) -> int:
    db = get_db()
    docs = list(db.kb_chunks.find({}, {"_id": 0, "chunk_id": 1, "text": 1, "vector": 1}))
    if not docs:
        raise SystemExit("polaris.kb_chunks vacía — corre `python -m src.vectorstore` primero.")
    # redondear a 6 decimales: imperceptible para cosine y baja ~40% el peso del bundle
    for d in docs:
        d["vector"] = [round(x, 6) for x in d["vector"]]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(docs, fh, ensure_ascii=False)  # compacto: es data, no para leer a mano
    return len(docs)


if __name__ == "__main__":
    n = export()
    kb = round(os.path.getsize(OUT) / 1024)
    print(f"exportados {n} chunks+vectores → {OUT} ({kb} KB)")
