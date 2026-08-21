"""Tests unitarios de metrics.py — casos chicos calculados a mano (criterio 10.3).

Estos tests son la evidencia de que el medidor mide bien: un Recall mal
implementado invalida TODAS las comparaciones v1 vs v2 (criterio 10.5).

Run:  uv run python -m src.eval.test_metrics   (también los levanta pytest)
"""

from __future__ import annotations

from src.eval import metrics

# ranking de referencia para varios tests: el esperado "b" aparece en la posición 3
RANKING = ["x", "y", "b", "z", "w"]


def test_recall_at_1() -> None:
    assert metrics.recall_at_1({"a"}, ["a", "b", "c"]) == 1.0
    assert metrics.recall_at_1({"a"}, ["b", "a", "c"]) == 0.0  # está, pero no de primero
    assert metrics.recall_at_1({"a"}, []) == 0.0
    # basta con que el top-1 sea CUALQUIERA de los esperados
    assert metrics.recall_at_1({"a", "b"}, ["b", "z"]) == 1.0


def test_recall_at_k() -> None:
    assert metrics.recall_at_k({"b"}, RANKING, k=5) == 1.0   # b en posición 3 ≤ 5
    assert metrics.recall_at_k({"b"}, RANKING, k=2) == 0.0   # b en posición 3 > 2
    assert metrics.recall_at_k({"q"}, RANKING, k=5) == 0.0   # no aparece
    assert metrics.recall_at_k({"w", "q"}, RANKING, k=5) == 1.0  # w en posición 5


def test_precision_at_k() -> None:
    # 2 esperados dentro del top-5 → 2/5
    assert metrics.precision_at_k({"y", "w"}, RANKING, k=5) == 2 / 5
    # solo cuenta la intersección DENTRO del top-k: con k=2 queda solo "y" → 1/2
    assert metrics.precision_at_k({"y", "w"}, RANKING, k=2) == 1 / 2
    assert metrics.precision_at_k(set(), RANKING, k=5) == 0.0


def test_mrr() -> None:
    # primer esperado en posición 3 → 1/3 (calculado a mano)
    assert metrics.mrr({"b"}, RANKING) == 1 / 3
    # con dos esperados manda el que aparece PRIMERO: "y" en posición 2 → 1/2
    assert metrics.mrr({"b", "y"}, RANKING) == 1 / 2
    assert metrics.mrr({"q"}, RANKING) == 0.0  # ausente → 0
    assert metrics.mrr({"x"}, RANKING) == 1.0  # top-1 → 1


def test_percentil_nearest_rank() -> None:
    valores = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    # nearest-rank con n=10: p50 → ceil(5)=5º elemento = 50; p95 → ceil(9.5)=10º = 100
    assert metrics.percentil(valores, 50) == 50.0
    assert metrics.percentil(valores, 95) == 100.0
    assert metrics.percentil([7.0], 95) == 7.0
    assert metrics.percentil([], 50) == 0.0
    # no depende del orden de entrada
    assert metrics.percentil([30.0, 10.0, 20.0], 50) == 20.0


def test_answer_type_match() -> None:
    # score bajo el umbral 0.50 → el "no sé" honesto se gatilla → match
    assert metrics.answer_type_match("refused_out_of_domain", 0.38) == 1.0
    assert metrics.answer_type_match("no_evidence", 0.49) == 1.0
    # score alto → el sistema respondería con falsa confianza → no match
    assert metrics.answer_type_match("no_evidence", 0.61) == 0.0
    # el umbral es estricto: 0.50 exacto NO gatilla (< 0.50)
    assert metrics.answer_type_match("no_evidence", 0.50) == 0.0
    # a una query con chunks esperados no se le chequea answer_type
    try:
        metrics.answer_type_match("grounded", 0.9)
        raise AssertionError("debió levantar ValueError")
    except ValueError:
        pass


def test_evaluar_query_elegible() -> None:
    fila = {"id": "q1", "lang": "es", "categoria": "tipica",
            "expected_chunks": ["b"], "expected_answer_type": "grounded"}
    r = metrics.evaluar_query(fila, RANKING, top1_score=0.8, k=5)
    assert r["elegible"] is True
    assert r["recall_1"] == 0.0 and r["recall_k"] == 1.0
    assert r["precision_k"] == 1 / 5 and r["mrr"] == 1 / 3


def test_evaluar_query_no_elegible() -> None:
    fila = {"id": "q2", "lang": "en", "categoria": "fuera_de_dominio",
            "expected_chunks": [], "expected_answer_type": "refused_out_of_domain"}
    r = metrics.evaluar_query(fila, RANKING, top1_score=0.42, k=5)
    assert r["elegible"] is False and r["answer_type_ok"] == 1.0


def test_agregar() -> None:
    # 2 elegibles calculadas a mano: recall_1 medio = (1+0)/2, mrr medio = (1 + 1/2)/2
    resultados = [
        {"id": "a", "lang": "es", "categoria": "tipica", "elegible": True, "top1_score": 0.9,
         "recall_1": 1.0, "recall_k": 1.0, "precision_k": 0.2, "mrr": 1.0},
        {"id": "b", "lang": "en", "categoria": "tipica", "elegible": True, "top1_score": 0.7,
         "recall_1": 0.0, "recall_k": 1.0, "precision_k": 0.4, "mrr": 0.5},
        {"id": "c", "lang": "es", "categoria": "fuera_de_dominio", "elegible": False,
         "top1_score": 0.3, "answer_type_ok": 1.0},
    ]
    ag = metrics.agregar(resultados, latencias_ms=[100.0, 200.0, 300.0], costo_por_query=0.00002, k=5)
    assert ag["global"]["n"] == 2
    assert ag["global"]["recall_1"] == 0.5
    assert ag["global"]["mrr"] == 0.75
    assert ag["global"]["precision_5"] == (0.2 + 0.4) / 2
    # la fuera_de_dominio NO contamina los agregados por idioma (es: solo "a")
    assert ag["por_idioma"]["es"]["n"] == 1 and ag["por_idioma"]["es"]["mrr"] == 1.0
    assert ag["answer_type"]["n"] == 1 and ag["answer_type"]["aciertos"] == 1
    assert ag["latencia_p50_ms"] == 200.0 and ag["latencia_p95_ms"] == 300.0


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
    print(f"{len(tests)} tests de metrics.py ok ✔")


if __name__ == "__main__":
    main()
