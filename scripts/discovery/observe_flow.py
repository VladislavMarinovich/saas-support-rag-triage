"""Discovery observacional del flow RAG de Polaris — Fase 0.b del Plan técnico v2.

Corre el hot path del Worker localmente en Python contra Vertex AI real e
instrumenta cada etapa para observar qué datos produce el sistema hoy. El
objetivo NO es evaluar calidad; es descubrir qué campos podemos capturar en el
schema BQ. La calidad se mide en Fase 1 (baseline) con eval framework separado.

Cada etapa emite un trace estructurado en formato XES-lite (case_id, activity,
timestamp, resource, data) a `specs/001-polaris-v2/discovery/traces.jsonl`,
compatible con process mining (PM4Py) futuro.

Auth: ADC (`gcloud auth application-default login`) sobre `polaris-triage-demo`.
Presupuesto estimado: < USD 0.01 total para 30 queries.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import types

# rutas relativas a la raiz del repo
REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / "kb"
QUERIES_PATH = REPO_ROOT / "scripts" / "discovery" / "queries.jsonl"
DISCOVERY_DIR = REPO_ROOT / "specs" / "001-polaris-v2" / "discovery"
TRACES_PATH = DISCOVERY_DIR / "traces.jsonl"
SUMMARY_PATH = DISCOVERY_DIR / "summary.md"

# modelos (mismos que el Worker actual segun ADR y polaris_estado_actual)
PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "polaris-triage-demo")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
EMBED_MODEL = "text-embedding-005"
GEN_MODEL = "gemini-2.5-flash-lite"

# precios oficiales Vertex AI en USD (fuente: cloud.google.com/vertex-ai/pricing)
PRICE_EMBED_PER_1K_TOKENS = 0.000025
PRICE_GEN_INPUT_PER_1M = 0.075   # gemini-2.5-flash-lite input
PRICE_GEN_OUTPUT_PER_1M = 0.30   # gemini-2.5-flash-lite output

# top-K chunks a recuperar
TOP_K = 5


def now_iso() -> str:
    """Timestamp UTC en formato ISO-8601."""
    return datetime.now(timezone.utc).isoformat()


def load_kb_chunks() -> list[dict]:
    """Chunkea la KB por secciones H2. Cada chunk = titulo + heading + cuerpo.

    Replica la estrategia estructural declarada en la Spec sin depender de MongoDB.
    """
    chunks = []
    for md_path in sorted(KB_DIR.glob("*.md")):
        source = md_path.stem
        title = ""
        current_heading = None
        current_body: list[str] = []

        def flush() -> None:
            """Guarda el bloque actual como chunk si tiene contenido."""
            if current_heading is None:
                return
            body = "\n".join(current_body).strip()
            if not body or "still stuck?" in body.lower():
                return
            chunk_text = f"{title}\n\n## {current_heading}\n\n{body}"
            chunks.append(
                {
                    "chunk_id": f"{source}::{current_heading.lower().replace(' ', '-')}",
                    "source": source,
                    "title": title,
                    "heading": current_heading,
                    "text": chunk_text,
                }
            )

        for line in md_path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not title:
                title = stripped[2:].strip()
            elif stripped.startswith("## "):
                flush()
                current_heading = stripped[3:].strip()
                current_body = []
            elif current_heading is not None:
                current_body.append(line)
        flush()

    return chunks


def dot(a: list[float], b: list[float]) -> float:
    """Producto punto — con vectores normalizados equivale a similitud coseno."""
    return sum(x * y for x, y in zip(a, b))


def normalize(vec: list[float]) -> list[float]:
    """Normaliza a norma 1 para que dot product == cosine similarity."""
    norm = sum(x * x for x in vec) ** 0.5
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def build_prompt(question: str, hits: list[tuple[str, float, str]]) -> str:
    """Prompt grounded al estilo del Worker actual (src/rag.py)."""
    context = "\n\n".join(f"[{cid}] {text}" for cid, _score, text in hits)
    return (
        "You are a support assistant for Polaris, an analytics SaaS. Answer the "
        "customer's question using ONLY the knowledge-base excerpts provided.\n\n"
        "Rules:\n"
        "- If the excerpts answer the question, reply concisely, grounded only in them.\n"
        "- If the excerpts do NOT answer it, say so honestly. Never invent features.\n"
        "- Answer naturally in the same language as the question; do not mention 'excerpts'.\n\n"
        f"Knowledge-base excerpts:\n{context}\n\n"
        f"Customer question: {question}\n\n"
        "Answer:"
    )


def emit_trace(traces: list[dict], case_id: str, activity: str, resource: str, data: dict) -> None:
    """Anexa una linea al trace en formato XES-lite."""
    traces.append(
        {
            "case_id": case_id,
            "activity": activity,
            "timestamp": now_iso(),
            "resource": resource,
            "data": data,
        }
    )


def main() -> None:
    print(f"[boot] proyecto={PROJECT} location={LOCATION}")
    print(f"[boot] embed={EMBED_MODEL} gen={GEN_MODEL} top_k={TOP_K}")

    # 1. cliente Vertex via ADC (routing por vertexai=True, no AI Studio)
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

    # 2. cargar y chunkear la KB en memoria
    t0 = time.time()
    chunks = load_kb_chunks()
    print(f"[boot] KB chunks: {len(chunks)} (en {time.time() - t0:.2f}s)")

    # 3. embebe todos los chunks una sola vez
    t0 = time.time()
    chunk_texts = [c["text"] for c in chunks]
    kb_embeddings: list[list[float]] = []
    total_kb_tokens = 0
    # batching para bajar overhead (Vertex acepta hasta 250 textos por request)
    for i in range(0, len(chunk_texts), 100):
        batch = chunk_texts[i : i + 100]
        resp = client.models.embed_content(model=EMBED_MODEL, contents=batch)
        for emb in resp.embeddings:
            kb_embeddings.append(normalize(list(emb.values)))
        # tokens aproximados por caracter/4 — Vertex no siempre expone metadata
        total_kb_tokens += sum(len(t) for t in batch) // 4
    kb_embed_cost = (total_kb_tokens / 1000) * PRICE_EMBED_PER_1K_TOKENS
    print(
        f"[boot] KB embebida en {time.time() - t0:.2f}s "
        f"(~{total_kb_tokens} tokens, ~${kb_embed_cost:.5f})"
    )

    # 4. cargar corpus de queries
    queries = [json.loads(line) for line in QUERIES_PATH.read_text().splitlines() if line.strip()]
    print(f"[boot] corpus: {len(queries)} queries\n")

    # 5. correr el flow por cada query, instrumentando cada etapa
    traces: list[dict] = []
    summary: list[dict] = []
    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)

    total_query_tokens = 0
    total_gen_input_tokens = 0
    total_gen_output_tokens = 0

    for q in queries:
        case_id = str(uuid.uuid4())
        qtext = q["text"]
        print(f"[{q['id']}] ({q['lang']}/{q['category']}) {qtext[:60]}")

        # etapa 1: recepcion
        t_start = time.time()
        emit_trace(
            traces,
            case_id,
            "receive_query",
            "worker",
            {
                "query_id": q["id"],
                "query_text": qtext,
                "query_length_chars": len(qtext),
                "lang_declared": q["lang"],
                "category": q["category"],
            },
        )

        # etapa 2: embedding de la query
        t_embed = time.time()
        emb_resp = client.models.embed_content(model=EMBED_MODEL, contents=[qtext])
        qvec = normalize(list(emb_resp.embeddings[0].values))
        embed_latency_ms = int((time.time() - t_embed) * 1000)
        query_tokens = max(1, len(qtext) // 4)
        total_query_tokens += query_tokens
        emit_trace(
            traces,
            case_id,
            "embed_query",
            "vertex-embedding-005",
            {
                "vector_dim": len(qvec),
                "vector_head": qvec[:5],
                "approx_input_tokens": query_tokens,
                "latency_ms": embed_latency_ms,
                "cost_usd": (query_tokens / 1000) * PRICE_EMBED_PER_1K_TOKENS,
            },
        )

        # etapa 3: retrieval por cosine exacto
        t_retr = time.time()
        scores = [(chunks[i]["chunk_id"], dot(kb_embeddings[i], qvec), chunks[i]) for i in range(len(chunks))]
        scores.sort(key=lambda x: x[1], reverse=True)
        top = scores[:TOP_K]
        retr_latency_ms = int((time.time() - t_retr) * 1000)
        emit_trace(
            traces,
            case_id,
            "retrieve_dense",
            "in-memory-cosine",
            {
                "top_k": TOP_K,
                "candidates_evaluated": len(chunks),
                "top1_chunk_id": top[0][0],
                "top1_score": top[0][1],
                "top5_scores": [s for _cid, s, _c in top],
                "top3_chunk_ids": [cid for cid, _s, _c in top[:3]],
                "top3_headings": [c["heading"] for _cid, _s, c in top[:3]],
                "latency_ms": retr_latency_ms,
            },
        )

        # etapa 4: construccion del prompt
        hits_for_prompt = [(cid, s, c["text"]) for cid, s, c in top]
        prompt = build_prompt(qtext, hits_for_prompt)
        emit_trace(
            traces,
            case_id,
            "build_prompt",
            "worker",
            {
                "prompt_length_chars": len(prompt),
                "prompt_length_approx_tokens": len(prompt) // 4,
                "chunks_in_prompt": TOP_K,
            },
        )

        # etapa 5: generacion
        t_gen = time.time()
        gen_resp = client.models.generate_content(
            model=GEN_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=400),
        )
        gen_latency_ms = int((time.time() - t_gen) * 1000)
        answer = gen_resp.text or ""
        usage = gen_resp.usage_metadata
        input_tokens = getattr(usage, "prompt_token_count", None) or (len(prompt) // 4)
        output_tokens = getattr(usage, "candidates_token_count", None) or (len(answer) // 4)
        total_gen_input_tokens += input_tokens
        total_gen_output_tokens += output_tokens

        # heuristica simple: si el LLM cita algun chunk id o menciona una fuente
        cited = any(chunk_id in answer for chunk_id, _s, _c in top)
        grounded = not any(
            phrase in answer.lower()
            for phrase in [
                "i don't have",
                "no tengo informac",
                "polaris doesn't",
                "polaris no",
                "not covered",
                "no cubre",
                "cannot help",
            ]
        )

        emit_trace(
            traces,
            case_id,
            "generate_response",
            "vertex-gemini-2.5-flash-lite",
            {
                "answer_length_chars": len(answer),
                "answer_snippet": answer[:200],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": gen_latency_ms,
                "cost_usd": (input_tokens / 1_000_000) * PRICE_GEN_INPUT_PER_1M
                + (output_tokens / 1_000_000) * PRICE_GEN_OUTPUT_PER_1M,
                "cited_chunk_id_in_answer": cited,
                "grounded_answer_heuristic": grounded,
            },
        )

        # etapa 6: entrega al usuario (fin del hot path)
        total_latency_ms = int((time.time() - t_start) * 1000)
        emit_trace(
            traces,
            case_id,
            "send_response",
            "worker",
            {
                "total_latency_ms": total_latency_ms,
            },
        )

        summary.append(
            {
                "id": q["id"],
                "lang": q["lang"],
                "category": q["category"],
                "top1_score": top[0][1],
                "top1_heading": top[0][2]["heading"],
                "latency_ms": total_latency_ms,
                "grounded": grounded,
                "answer_snippet": answer[:120].replace("\n", " "),
            }
        )

    # 6. persistir traces (formato XES-lite: 1 evento por linea)
    with TRACES_PATH.open("w") as f:
        for tr in traces:
            f.write(json.dumps(tr, ensure_ascii=False) + "\n")

    # 7. resumen ejecutivo en markdown
    total_gen_cost = (
        (total_gen_input_tokens / 1_000_000) * PRICE_GEN_INPUT_PER_1M
        + (total_gen_output_tokens / 1_000_000) * PRICE_GEN_OUTPUT_PER_1M
    )
    total_query_embed_cost = (total_query_tokens / 1000) * PRICE_EMBED_PER_1K_TOKENS
    total_cost = kb_embed_cost + total_query_embed_cost + total_gen_cost

    latencies = [s["latency_ms"] for s in summary]
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2]
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]

    grounded_count = sum(1 for s in summary if s["grounded"])

    md = []
    md.append("# Discovery — Resumen ejecutivo")
    md.append("")
    md.append(f"Fecha: {now_iso()}")
    md.append(f"Corpus: {len(queries)} queries · Chunks KB: {len(chunks)}")
    md.append("")
    md.append("## Costos")
    md.append("")
    md.append(f"- KB embed (una vez): ~${kb_embed_cost:.5f}")
    md.append(f"- Query embeds (30): ~${total_query_embed_cost:.5f}")
    md.append(f"- Generacion (30): ~${total_gen_cost:.5f}")
    md.append(f"- **Total: ~${total_cost:.5f}**")
    md.append("")
    md.append("## Latencia end-to-end (ms)")
    md.append("")
    md.append(f"- p50: {p50} ms")
    md.append(f"- p95: {p95} ms")
    md.append(f"- min: {min(latencies)} ms · max: {max(latencies)} ms")
    md.append("")
    md.append("## Grounding heuristico")
    md.append("")
    md.append(f"- Respondio con evidencia: {grounded_count}/{len(summary)}")
    md.append(f"- Dijo 'no se' o rechazo: {len(summary) - grounded_count}/{len(summary)}")
    md.append("")
    md.append("## Detalle por query")
    md.append("")
    md.append("| ID | lang | categoria | top1 score | top1 heading | latencia | grounded | respuesta |")
    md.append("|---|---|---|---|---|---|---|---|")
    for s in summary:
        md.append(
            f"| {s['id']} | {s['lang']} | {s['category']} | "
            f"{s['top1_score']:.3f} | {s['top1_heading'][:40]} | "
            f"{s['latency_ms']} ms | {'sí' if s['grounded'] else 'no'} | "
            f"{s['answer_snippet']} |"
        )

    SUMMARY_PATH.write_text("\n".join(md) + "\n")

    print()
    print(f"[ok] traces escritos a {TRACES_PATH.relative_to(REPO_ROOT)}")
    print(f"[ok] summary escrito a {SUMMARY_PATH.relative_to(REPO_ROOT)}")
    print(f"[ok] costo total: ~${total_cost:.5f}")


if __name__ == "__main__":
    main()
