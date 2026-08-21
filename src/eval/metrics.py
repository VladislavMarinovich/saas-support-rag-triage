"""Métricas de retrieval del eval — implementación a mano de eval.md §3.

Funciones puras sobre (chunks esperados E, ranking recuperado R): sin llamadas
externas, sin estado, deterministas. La agregación excluye de Recall/Precision/MRR
toda query sin chunk correcto etiquetado (`expected_chunks: []` — las
fuera_de_dominio por regla del spec, y las ambiguas sin respuesta defendible);
esas se evalúan aparte por answer_type contra el umbral empírico de score.

Tests: `uv run python -m src.eval.test_metrics` (casos calculados a mano).
"""

from __future__ import annotations

# umbral empírico de confianza del discovery (findings.md §4): top1_score < 0.50
# ⇒ el sistema debe responder "no sé" honesto en vez de forzar una respuesta
UMBRAL_NO_SE = 0.50


def recall_at_1(expected: set[str], ranking: list[str]) -> float:
    """1.0 si el primer chunk recuperado es uno de los esperados."""
    return 1.0 if ranking and ranking[0] in expected else 0.0


def recall_at_k(expected: set[str], ranking: list[str], k: int = 5) -> float:
    """1.0 si ALGÚN esperado aparece en el top-k (¿la respuesta llega al contexto?)."""
    return 1.0 if expected & set(ranking[:k]) else 0.0


def precision_at_k(expected: set[str], ranking: list[str], k: int = 5) -> float:
    """|E ∩ top-k| / k — cuánto del contexto que entra al prompt es señal."""
    if k <= 0:
        return 0.0
    return len(expected & set(ranking[:k])) / k


def mrr(expected: set[str], ranking: list[str]) -> float:
    """1/rank del PRIMER esperado que aparece en el ranking; 0 si no aparece."""
    for i, chunk_id in enumerate(ranking, start=1):
        if chunk_id in expected:
            return 1.0 / i
    return 0.0


def percentil(valores: list[float], p: float) -> float:
    """Percentil por nearest-rank (determinista, sin interpolación).

    Mismo criterio que el resumen del discovery: ordenar y tomar el elemento
    en la posición ceil(p/100 · n) (índice base-1), con p50 = mediana inferior.
    """
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    if p >= 100:
        return ordenados[-1]
    # nearest-rank: índice base-0 = ceil(p/100 * n) - 1, acotado al rango
    import math

    idx = max(0, min(len(ordenados) - 1, math.ceil(p / 100 * len(ordenados)) - 1))
    return ordenados[idx]


def answer_type_esperado_no_grounded(expected_answer_type: str) -> bool:
    """True si la etiqueta espera que el sistema NO responda con evidencia."""
    return expected_answer_type in ("no_evidence", "refused_out_of_domain")


def answer_type_match(expected_answer_type: str, top1_score: float) -> float:
    """Chequeo del "no sé" honesto (solo queries sin chunk esperado).

    El gatillo observable en v1 es el score: `top1_score < 0.50` debería activar
    la respuesta honesta. Match = la etiqueta espera no-grounded Y el score
    quedó bajo el umbral.
    """
    if not answer_type_esperado_no_grounded(expected_answer_type):
        raise ValueError("answer_type_match solo aplica a queries sin chunk esperado")
    return 1.0 if top1_score < UMBRAL_NO_SE else 0.0


def evaluar_query(fila: dict, ranking: list[str], top1_score: float, k: int = 5) -> dict:
    """Evalúa UNA query del corpus contra su ranking. Devuelve la fila de resultados.

    `elegible` marca si entra a Recall/Precision/MRR (tiene chunks esperados).
    """
    expected = set(fila["expected_chunks"])
    elegible = bool(expected)
    resultado = {
        "id": fila["id"],
        "lang": fila["lang"],
        "categoria": fila["categoria"],
        "elegible": elegible,
        "top1_score": top1_score,
    }
    if elegible:
        resultado.update(
            recall_1=recall_at_1(expected, ranking),
            recall_k=recall_at_k(expected, ranking, k),
            precision_k=precision_at_k(expected, ranking, k),
            mrr=mrr(expected, ranking),
        )
    else:
        resultado["answer_type_ok"] = answer_type_match(fila["expected_answer_type"], top1_score)
    return resultado


def _promedio(filas: list[dict], campo: str) -> float:
    return sum(f[campo] for f in filas) / len(filas) if filas else 0.0


def agregar(resultados: list[dict], latencias_ms: list[float], costo_por_query: float, k: int = 5) -> dict:
    """Agrega los resultados por-query en las métricas del reporte (eval.md §3).

    Devuelve agregados globales + por idioma + por categoría (solo elegibles),
    y la sección answer_type para las no elegibles.
    """
    elegibles = [r for r in resultados if r["elegible"]]
    no_elegibles = [r for r in resultados if not r["elegible"]]

    def bloque(filas: list[dict]) -> dict:
        return {
            "n": len(filas),
            "recall_1": _promedio(filas, "recall_1"),
            f"recall_{k}": _promedio(filas, "recall_k"),
            f"precision_{k}": _promedio(filas, "precision_k"),
            "mrr": _promedio(filas, "mrr"),
        }

    por_idioma = {
        lang: bloque([r for r in elegibles if r["lang"] == lang])
        for lang in sorted({r["lang"] for r in elegibles})
    }
    por_categoria = {
        cat: bloque([r for r in elegibles if r["categoria"] == cat])
        for cat in sorted({r["categoria"] for r in elegibles})
    }

    return {
        "global": bloque(elegibles),
        "por_idioma": por_idioma,
        "por_categoria": por_categoria,
        "latencia_p50_ms": percentil(latencias_ms, 50),
        "latencia_p95_ms": percentil(latencias_ms, 95),
        "costo_por_query_usd": costo_por_query,
        "answer_type": {
            "n": len(no_elegibles),
            "aciertos": sum(int(r["answer_type_ok"]) for r in no_elegibles),
            "detalle": [
                {
                    "id": r["id"],
                    "categoria": r["categoria"],
                    "top1_score": r["top1_score"],
                    "ok": bool(r["answer_type_ok"]),
                }
                for r in no_elegibles
            ],
        },
    }
