"""Reporte del eval en Markdown pegable en PR — formato de eval.md §6.

Render puro: recibe los agregados y la config y devuelve un string. Todo lo que
entra es determinista (métricas de cache congelado + fecha inyectada), así que
el mismo run produce byte a byte el mismo reporte — condición del criterio 10.4.
"""

from __future__ import annotations


def _fmt(x: float, dec: int = 2) -> str:
    return f"{x:.{dec}f}"


def _tabla_bloques(titulo: str, bloques: dict[str, dict], k: int) -> list[str]:
    """Tabla de desglose (por idioma o por categoría) con una fila por grupo."""
    lineas = [
        f"### {titulo}",
        "",
        f"| Grupo | n | Recall@1 | Recall@{k} | Precision@{k} | MRR |",
        "|---|---|---|---|---|---|",
    ]
    for nombre, b in bloques.items():
        lineas.append(
            f"| {nombre} | {b['n']} | {_fmt(b['recall_1'])} | {_fmt(b[f'recall_{k}'])} "
            f"| {_fmt(b[f'precision_{k}'])} | {_fmt(b['mrr'])} |"
        )
    lineas.append("")
    return lineas


def render(config: dict, agregados: dict, fecha: str) -> str:
    """Arma el reporte completo. `config` trae la identidad exacta del experimento."""
    k = config["top_k"]
    g = agregados["global"]
    at = agregados["answer_type"]

    lineas = [
        f"## Eval — {fecha} · corpus {config['corpus_version']} · "
        f"KB {config['kb_chunks']} chunks (hash {config['kb_hash']})",
        "",
        f"| Métrica | {config['nombre']} |",
        "|---|---|",
        f"| Recall@1 | {_fmt(g['recall_1'])} |",
        f"| Recall@{k} | {_fmt(g[f'recall_{k}'])} |",
        f"| Precision@{k} | {_fmt(g[f'precision_{k}'])} |",
        f"| MRR | {_fmt(g['mrr'])} |",
        f"| p50 retrieval (ms) | {agregados['latencia_p50_ms']:.0f} |",
        f"| p95 retrieval (ms) | {agregados['latencia_p95_ms']:.0f} |",
        f"| Costo/query | ${agregados['costo_por_query_usd']:.6f} |",
        f"| answer_type match | {at['aciertos']}/{at['n']} |",
        "",
        f"Sobre {g['n']} queries con chunk esperado; las {at['n']} sin chunk esperado "
        "(fuera de dominio y ambiguas sin respuesta) se evalúan solo por answer_type.",
        "",
    ]

    lineas += _tabla_bloques("Por idioma", agregados["por_idioma"], k)
    lineas += _tabla_bloques("Por categoría", agregados["por_categoria"], k)

    lineas += [
        "### answer_type — el «no sé» honesto (umbral top1_score < 0.50)",
        "",
        "| ID | Categoría | top1_score | ¿gatilla el umbral? |",
        "|---|---|---|---|",
    ]
    for d in at["detalle"]:
        lineas.append(
            f"| {d['id']} | {d['categoria']} | {d['top1_score']:.3f} | {'sí' if d['ok'] else 'NO'} |"
        )

    lineas += [
        "",
        "### Config exacta",
        "",
        f"- **Config:** {config['nombre']} — {config['descripcion']}",
        f"- **KB:** {config['kb_chunks']} chunks (chunker discovery `source::heading`) · hash índice `{config['kb_hash']}`",
        f"- **Corpus:** {config['corpus_version']} · sha `{config['corpus_hash']}`",
        f"- **Embeddings:** {config['embed_model']} (Vertex) · top-K = {k}",
        f"- **Fecha:** {fecha}",
        f"- **Costo del corpus embebido:** ${config['costo_total_usd']:.5f} "
        f"(queries + KB, derivado de tokens; el gasto incremental real del run se imprime en consola)",
        "- **Latencia:** percentiles del embed de query (Vertex, congelados en cache); "
        "el cosine in-memory agrega ~1-3 ms y se reporta en consola (discovery §1).",
        "",
    ]
    return "\n".join(lineas)
