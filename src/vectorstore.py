"""KB vector store sobre MongoDB — retrieval por cosine exacto (sin vector DB).

Decisión ADR 0001: la KB es pequeña y estática (89 chunks). Un vector DB dedicado
(Pinecone) solo agregaba un servicio externo, un secreto y un hop de red sin
beneficio medible (benchmark: top hit 0.824 in-memory vs 0.825 Pinecone). Aquí los
chunks *y* sus embeddings viven en Mongo (el único system-of-record) y el retrieval
es cosine exacto (brute-force, O(n·d)) calculado en la app — instantáneo a 89 vectores.

Indexado:  chunk KB -> embed (Vertex) -> upsert a `polaris.kb_chunks`.
Query:     embed la pregunta -> cosine exacto contra los vectores cacheados en memoria.

Auth: MONGODB_URI (Mongo) + ADC (Vertex, embeddings) en el .env gitignoreado.
Run:  python -m src.vectorstore   (indexa la KB y corre una query de ejemplo)
"""

from __future__ import annotations

import numpy as np

from src.chunk_kb import chunk_kb
from src.embed import embed_texts
from src.mongo_store import get_db

KB_CHUNKS = "kb_chunks"  # colección en la db `polaris`

# Cache en memoria de (chunk_ids, textos, matriz de vectores normalizados). La KB
# es estática, así que la cargamos una vez desde Mongo y reusamos entre queries.
_cache: tuple[list[str], list[str], np.ndarray] | None = None


def _normalize(mat: np.ndarray) -> np.ndarray:
    """Normaliza cada fila a norma 1 para que el dot product == cosine."""
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # evita división por cero en un vector degenerado
    return mat / norms


def index_kb() -> int:
    """Chunk + embed la KB y hace upsert de cada chunk a `polaris.kb_chunks`.

    Cada doc guarda el texto Y su vector, así Mongo es el único store (ADR 0001).
    Idempotente: upsert por chunk_id, seguro de re-correr.
    """
    from pymongo import ReplaceOne

    # 1. partir la KB en chunks y embeber el texto de cada uno
    chunks = chunk_kb()
    vectors = embed_texts([c.text for c in chunks])

    db = get_db()
    col = db[KB_CHUNKS]
    col.create_index("chunk_id", unique=True)

    # 2. un doc por chunk: metadata + texto + vector (para cosine en la app)
    ops = [
        ReplaceOne(
            {"chunk_id": c.chunk_id},
            {
                "chunk_id": c.chunk_id,
                "source": c.source,
                "title": c.title,
                "heading": c.heading or "",
                "text": c.text,
                "vector": [float(x) for x in v],  # BSON no acepta numpy floats
            },
            upsert=True,
        )
        for c, v in zip(chunks, vectors)
    ]
    col.bulk_write(ops, ordered=False)

    global _cache
    _cache = None  # invalida el cache: la colección cambió
    return col.count_documents({})


def _load_cache() -> tuple[list[str], list[str], np.ndarray]:
    """Carga (una vez) todos los vectores de la KB desde Mongo a memoria."""
    global _cache
    if _cache is None:
        db = get_db()
        docs = list(db[KB_CHUNKS].find({}, {"chunk_id": 1, "text": 1, "vector": 1}))
        if not docs:
            raise RuntimeError(
                "polaris.kb_chunks está vacía — corre `python -m src.vectorstore` "
                "para indexar la KB primero."
            )
        ids = [d["chunk_id"] for d in docs]
        texts = [d["text"] for d in docs]
        mat = _normalize(np.asarray([d["vector"] for d in docs], dtype=np.float32))
        _cache = (ids, texts, mat)
    return _cache


def search(query: str, top_k: int = 3):
    """Embebe la query y devuelve los top_k chunks más cercanos por cosine exacto.

    DEVUELVE `[(chunk_id, score, text)]` — mismo shape que la versión Pinecone, así
    `rag.py` (que hace `for cid, _score, text in hits`) no se toca.
    """
    ids, texts, mat = _load_cache()
    # embeber la query con el MISMO modelo, normalizar, y cosine == dot product
    qv = _normalize(np.asarray([embed_texts([query])[0]], dtype=np.float32))[0]
    scores = mat @ qv  # (n,) similitud coseno contra cada chunk
    top = np.argsort(-scores)[:top_k]  # índices de los top_k por score desc
    return [(ids[i], float(scores[i]), texts[i]) for i in top]


if __name__ == "__main__":
    n = index_kb()
    print(f"indexados {n} chunks en Mongo (`polaris.{KB_CHUNKS}`)")

    q = "my dashboard is blank and I think our google ads connector expired, how do I fix it?"
    print(f"\nQUERY: {q}\n")
    for rank, (cid, score, text) in enumerate(search(q), 1):
        print(f"  #{rank}  score={score:.3f}  [{cid}]")
        print("  " + text.replace("\n", " ")[:170])
