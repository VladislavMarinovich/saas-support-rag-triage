"""Cache de embeddings del eval — segundo run = USD 0 y números idénticos.

Cada texto embebido (query o chunk de KB) se guarda en `src/eval/cache/` como
`{sha256(model + texto)}.json` con su vector, la latencia real de la llamada a
Vertex y el costo aproximado. El cache está gitignoreado (eval.md §5).

El cache no es solo ahorro: es la base del DETERMINISMO del eval (criterio 10.4,
"mismo corpus + misma config = mismos números"). Vertex no garantiza embeddings
bit-idénticos entre llamadas; con cache, a partir del primer run los vectores —
y por lo tanto los rankings y las latencias reportadas — quedan congelados.

Reutiliza `src.embed.embed_texts` (el MISMO modelo y endpoint que indexa la KB
de producción, ADR 0001) — acá solo se agrega la capa de persistencia.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from src.embed import EMBED_MODEL, embed_texts

CACHE_DIR = Path(__file__).resolve().parent / "cache"

# precio oficial Vertex para text-embedding-005 (mismo valor que usó el discovery)
PRICE_EMBED_PER_1K_TOKENS = 0.000025


def _cache_path(text: str, model: str) -> Path:
    clave = hashlib.sha256(f"{model}\x00{text}".encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{clave}.json"


def _costo_aprox(text: str) -> float:
    """Costo aproximado del embed: tokens ~ chars/4 (misma heurística del discovery)."""
    tokens = max(1, len(text) // 4)
    return (tokens / 1000) * PRICE_EMBED_PER_1K_TOKENS


def get_embedding(text: str, model: str | None = None) -> dict:
    """Devuelve `{vector, latency_ms, cost_usd, cache_hit}` para un texto.

    En miss llama a Vertex (una query por llamada, para capturar la latencia
    real por query) y persiste el resultado; en hit no cuesta ni un token.
    """
    model = model or EMBED_MODEL
    path = _cache_path(text, model)
    if path.exists():
        entrada = json.loads(path.read_text(encoding="utf-8"))
        entrada["cache_hit"] = True
        return entrada

    t0 = time.time()
    vector = embed_texts([text], model=model)[0]
    latency_ms = int((time.time() - t0) * 1000)
    entrada = {
        "model": model,
        "vector": [float(x) for x in vector],
        "latency_ms": latency_ms,
        "cost_usd": _costo_aprox(text),
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entrada), encoding="utf-8")
    entrada["cache_hit"] = False
    return entrada


def get_embeddings_batch(texts: list[str], model: str | None = None) -> list[dict]:
    """Como `get_embedding` pero embebe los misses en UN batch (para la KB).

    La latencia individual no es significativa en batch, así que se guarda la
    latencia del batch prorrateada — para chunks de KB no se reporta latencia.
    """
    model = model or EMBED_MODEL
    resultados: list[dict | None] = []
    misses: list[int] = []
    for i, text in enumerate(texts):
        path = _cache_path(text, model)
        if path.exists():
            entrada = json.loads(path.read_text(encoding="utf-8"))
            entrada["cache_hit"] = True
            resultados.append(entrada)
        else:
            resultados.append(None)
            misses.append(i)

    if misses:
        t0 = time.time()
        vectores = embed_texts([texts[i] for i in misses], model=model)
        batch_ms = int((time.time() - t0) * 1000)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        for j, i in enumerate(misses):
            entrada = {
                "model": model,
                "vector": [float(x) for x in vectores[j]],
                "latency_ms": batch_ms // len(misses),
                "cost_usd": _costo_aprox(texts[i]),
            }
            _cache_path(texts[i], model).write_text(json.dumps(entrada), encoding="utf-8")
            entrada["cache_hit"] = False
            resultados[i] = entrada

    return resultados  # type: ignore[return-value]
