"""Genera la respuesta de cada ticket y la persiste en Mongo (alimenta la UI/foro).

Estrategia FinOps (ver docs/costs.md): el LLM se usa SOLO donde agrega valor.
  - routing == kb_autoresolve  -> respuesta RAG (LLM, grounded en la KB).
  - cualquier otro routing      -> ack TEMPLADO de cara al cliente (sin LLM, ~$0):
    saluda, confirma recepción, dice a qué equipo se enrutó y fija una expectativa
    de tiempo según la prioridad. No resuelve — acusa recibo con calidez.

Usa el `routing` gold que ya trae cada ticket (no re-clasifica: aquí producimos
respuestas, no evaluamos el clasificador — eso ya se midió en classify.py).

Run:  python -m src.responses --sample 15         # muestra mixta, imprime + guarda
      python -m src.responses --sample 15 --dry    # solo imprime, no toca Mongo
"""

from __future__ import annotations

import argparse
import json
import re

from src.rag import answer as rag_answer

TICKETS_FILE = "data/tickets_v2.jsonl"

# Nombre del equipo (de cara al cliente) por cada destino de escalación.
TEAM = {
    "engineering": "engineering team",
    "sales_success": "accounts team",
    "retention": "customer success team",
    "security_incident": "security team",
}

# Expectativa de tiempo de respuesta según la prioridad del ticket (SLA suave).
# Las prioridades del dataset son: critical / high / medium / low.
SLA = {
    "critical": "within a few hours",
    "high": "within one business day",
    "medium": "within 1–2 business days",
    "low": "within 2–3 business days",
}


def _ack_template(ticket: dict) -> str:
    """Ack de cara al cliente para un ticket escalado (determinista, sin LLM).

    Varía por equipo y prioridad; una pizca de variación en el saludo (derivada
    del ticket_id) evita que 9.900 acks se lean idénticos.
    """
    team = TEAM.get(ticket["routing"], "support team")
    sla = SLA.get(ticket["priority"], "within 1–2 business days")

    # el asunto del cliente viene ruidoso ("...slack???"); limpiamos puntuación
    # final. Si queda vacío (o el ticket no traía asunto), usamos el topic.
    subject = re.sub(r"[\s?!.,]+$", "", (ticket.get("subject") or "").strip())
    topic = subject or f"your {ticket['topic']} issue"

    # saludo elegido de forma determinista (mismo ticket -> mismo saludo)
    greetings = ("Hi there", "Hello", "Hi")
    greet = greetings[sum(ord(c) for c in ticket["ticket_id"]) % len(greetings)]

    # línea extra solo cuando de verdad corre prisa (crítico o seguridad)
    urgent = ticket["priority"] == "critical" or ticket["routing"] == "security_incident"
    priority_line = " We're treating this as a priority." if urgent else ""

    return (
        f"{greet} — thanks for reaching out about {topic}. "
        f"We've received your message and routed it to our {team}."
        f"{priority_line} A specialist will follow up {sla}.\n\n"
        f"— The Polaris Support Team"
    )


def build_response(ticket: dict) -> dict:
    """Devuelve {response, response_kind} para un ticket según su routing gold."""
    if ticket["routing"] == "kb_autoresolve":
        reply, _hits = rag_answer(ticket["body"])
        return {"response": reply.strip(), "response_kind": "rag"}
    return {"response": _ack_template(ticket), "response_kind": "templated_ack"}


def _stratified_sample(tickets: list[dict], n: int) -> list[dict]:
    """Muestra que garantiza mezcla: RAG + cada equipo escalado + cada EVENTO.

    El foro es más vendedor si muestra los picos (lanzamientos de conectores,
    outages), así que reservamos cupo para tickets de cada event_id además del
    reparto por routing. Dedup por ticket_id al final.
    """
    by_routing: dict[str, list[dict]] = {}
    by_event: dict[str, list[dict]] = {}
    for t in tickets:
        by_routing.setdefault(t["routing"], []).append(t)
        if t.get("event_id"):
            by_event.setdefault(t["event_id"], []).append(t)

    picks: list[dict] = []
    # 1. cupo garantizado para eventos: unos pocos de cada lanzamiento/outage
    for ev_tickets in by_event.values():
        picks.extend(ev_tickets[:6])

    # 2. ~half kb_autoresolve (donde importa la calidad RAG)
    kb = by_routing.get("kb_autoresolve", [])
    picks.extend(kb[: max(1, n // 2)])

    # 3. resto repartido entre los equipos escalados
    others = [r for r in by_routing if r != "kb_autoresolve"]
    per = max(1, (n - len(picks)) // max(1, len(others)))
    for r in others:
        picks.extend(by_routing[r][:per])

    # dedup preservando orden (un ticket de evento no debe contar dos veces)
    seen, unique = set(), []
    for t in picks:
        if t["ticket_id"] not in seen:
            seen.add(t["ticket_id"])
            unique.append(t)
    return unique[:n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=15, help="cuántos tickets procesar")
    ap.add_argument("--dry", action="store_true", help="solo imprime, no escribe en Mongo")
    args = ap.parse_args()

    tickets = [json.loads(line) for line in open(TICKETS_FILE, encoding="utf-8")]
    sample = _stratified_sample(tickets, args.sample)

    # generar la respuesta de cada ticket e imprimirla para revisión visual
    results = []
    for t in sample:
        r = build_response(t)
        results.append((t, r))
        print("=" * 78)
        print(f"[{t['ticket_id']}]  routing={t['routing']}  priority={t['priority']}"
              f"  topic={t['topic']}  -> {r['response_kind']}")
        print(f"TICKET:   {t['body'][:200].strip()}")
        print(f"RESPONSE: {r['response']}")
        print()

    if args.dry:
        print("(dry-run — no se escribió nada en Mongo)")
        return

    # persistir: enriquecer cada doc del ticket con su respuesta (idempotente)
    from src.mongo_store import get_db

    db = get_db()
    for t, r in results:
        db.tickets.update_one({"ticket_id": t["ticket_id"]}, {"$set": r})
    kinds = {}
    for _t, r in results:
        kinds[r["response_kind"]] = kinds.get(r["response_kind"], 0) + 1
    print(f"guardadas {len(results)} respuestas en Mongo (`polaris.tickets`): {kinds}")


if __name__ == "__main__":
    main()
