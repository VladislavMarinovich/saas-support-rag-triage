// Vista cliente — envía el ticket al Worker y muestra la respuesta en vivo.
// Contrato con el Worker (fase 2):
//   POST /api/triage  { subject, message, turnstileToken }
//   -> { answer: string(markdown), triage: {topic,type,priority,routing,sentiment}, kind: "rag"|"escalated" }
//
// Modo mock (?mock=1): responde con datos canned, sin llamar al Worker — sirve para
// verificar la UI antes de que el backend exista. En producción (sin el flag) pega al Worker.

const $ = (s) => document.querySelector(s);
const MOCK = new URLSearchParams(location.search).has("mock");

// --- helpers de render (mismo mini-markdown seguro que el foro) ---
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pretty = (s) => String(s ?? "").replace(/_/g, " ");
const mdInline = (s) => s
  .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+|mailto:[^)\s]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener">$1</a>')
  .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
  .replace(/\*([^*\n]+)\*/g, "<em>$1</em>")
  .replace(/`([^`]+)`/g, "<code>$1</code>");

function mdToHtml(raw) {
  const lines = esc(raw).split("\n");
  let html = "", list = null;
  const closeList = () => { if (list) { html += `</${list}>`; list = null; } };
  for (const line of lines) {
    const t = line.trim();
    const ol = t.match(/^\d+\.\s+(.*)/), ul = t.match(/^[-*]\s+(.*)/);
    if (ol) { if (list !== "ol") { closeList(); html += "<ol>"; list = "ol"; } html += `<li>${mdInline(ol[1])}</li>`; }
    else if (ul) { if (list !== "ul") { closeList(); html += "<ul>"; list = "ul"; } html += `<li>${mdInline(ul[1])}</li>`; }
    else if (!t) { closeList(); }
    else { closeList(); html += `<p>${mdInline(t)}</p>`; }
  }
  closeList();
  return html;
}

// --- respuesta canned para el modo mock ---
function mockResponse(message) {
  return {
    answer: "I can help with that. Here's what to check:\n\n" +
      "1. **Open Connectors** — go to **Settings > Connectors** in your workspace.\n" +
      "2. **Check the status** — if a connector shows *expired*, click **Reconnect**.\n" +
      "3. **Wait for the next sync** — data refreshes on your schedule (typically within 1 hour).\n\n" +
      "If it still doesn't work after reconnecting, reach out at [support@polaris.app](mailto:support@polaris.app).",
    triage: { topic: "connectors", type: "how_to", priority: "medium", routing: "kb_autoresolve", sentiment: "neutral" },
    kind: "rag",
    sources: ["Reconnecting an expired connector", "How to connect Google Analytics 4"],
  };
}

// --- envío ---
async function submit(ev) {
  ev.preventDefault();
  const message = $("#message").value.trim();
  const subject = $("#subject").value.trim();
  $("#err").textContent = "";
  if (!message) { $("#err").textContent = "Please describe your issue."; return; }

  // token del captcha (en mock lo omitimos)
  const token = MOCK ? "mock" : (window.turnstile && turnstile.getResponse());
  if (!MOCK && !token) { $("#err").textContent = "Please complete the verification."; return; }

  const btn = $("#submit");
  btn.disabled = true; btn.textContent = "Sending…";

  // arma el hilo YA (el post del cliente) y streamea la respuesta dentro
  const refs = buildSkeleton({ subject, message });
  let answerText = "";
  const onToken = (t) => {
    answerText += t;
    refs.body.innerHTML = mdToHtml(answerText) + '<span class="cursor"></span>';
    refs.body.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  try {
    if (MOCK) {
      const m = mockResponse(message);
      for (const piece of (m.answer.match(/\S+\s*/g) || [])) { onToken(piece); await sleep(35); }
      finalizeReply(refs, m, answerText);
    } else {
      const res = await fetch("/api/triage", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject, message, turnstileToken: token }),
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      // consume el stream SSE: `token` (texto en vivo) + `result` (triage/fuentes al final)
      let result = null, streamErr = null;
      await readSSE(res, (event, data) => {
        if (event === "token") onToken(data.t || "");
        else if (event === "result") result = data;
        else if (event === "error") streamErr = data.detail || "stream error";
      });
      if (streamErr) throw new Error(streamErr);
      finalizeReply(refs, result || {}, answerText);
    }
  } catch (e) {
    $("#answer").hidden = true;
    $("#err").textContent = "Sorry, something went wrong. Please try again.";
    if (window.turnstile) turnstile.reset();
  } finally {
    btn.disabled = false; btn.textContent = "Send message";
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Lee un stream Server-Sent-Events y llama onEvent(event, obj) por cada bloque (\n\n).
async function readSSE(res, onEvent) {
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let sep;
    while ((sep = buf.indexOf("\n\n")) >= 0) {
      const raw = buf.slice(0, sep); buf = buf.slice(sep + 2);
      let event = "message", data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) { try { onEvent(event, JSON.parse(data)); } catch { /* ignora bloque parcial */ } }
    }
  }
}

// --- hilo: post original + esqueleto de la respuesta (se llena al streamear) ---
function buildSkeleton(asked) {
  const title = (asked.subject && asked.subject.trim()) || asked.message.slice(0, 60);
  $("#answer").hidden = false;
  $("#answer").innerHTML = `
    <div class="thread">
      <div class="post op">
        <div class="post-head"><span class="who">You</span><span class="dot">·</span><span class="when">just now</span></div>
        <div class="post-title">${esc(title)}</div>
        <div class="post-body">${esc(asked.message)}</div>
      </div>
      <div class="post reply">
        <div class="post-head"><span class="verified" id="verified">Polaris AI is typing…</span></div>
        <div class="response-body" id="ansbody"></div>
        <div id="replymeta"></div>
      </div>
    </div>`;
  return { body: $("#ansbody"), meta: $("#replymeta"), verified: $("#verified") };
}

// --- cierra la respuesta: badge final + fuentes + utilidad + triage colapsable ---
function finalizeReply(refs, data, answerText) {
  const isRag = data.kind === "rag";
  const t = data.triage || {};
  const team = pretty(t.routing || "the right team");
  // para "pedir humano": kb_autoresolve NO es un equipo -> cae a soporte general
  const humanTeam = t.routing && t.routing !== "kb_autoresolve" ? pretty(t.routing) : "support";
  const labels = [["topic", t.topic], ["type", t.type], ["priority", t.priority], ["routing", t.routing]]
    .filter(([, v]) => v);
  const sources = data.sources || [];

  refs.body.innerHTML = mdToHtml(answerText);  // quita el cursor, render final
  refs.verified.textContent = isRag ? "✓ Answered by Polaris AI" : "↗ Routed to " + team;

  refs.meta.innerHTML = `
    ${sources.length ? `<div class="sources"><span class="src-lbl">Sources</span>${
      sources.map((s) => `<span class="src-badge">${esc(s)}</span>`).join("")}</div>` : ""}
    <div class="helpful" id="helpful">
      <span class="hlp-q">Was this helpful?</span>
      <button class="hlp-btn" data-v="yes">Yes</button>
      <button class="hlp-btn" data-v="no">No</button>
      <button class="hlp-btn human" data-v="human">Request a human agent</button>
    </div>
    ${labels.length ? `<details class="triage-fold"><summary>How Polaris classified this</summary>
      <div class="labels">${labels.map(([k, v]) =>
        `<span class="chip"><b>${esc(k)}</b> ${esc(pretty(v))}</span>`).join("")}</div>
    </details>` : ""}`;

  $("#helpful").querySelectorAll(".hlp-btn").forEach((b) =>
    b.addEventListener("click", () => {
      const v = b.dataset.v;
      const msg = v === "human"
        ? `Got it — we've routed this to our ${humanTeam} team. A specialist will follow up.`
        : v === "yes" ? "Thanks — glad that helped! 🎉" : "Thanks for the feedback — we'll use it to improve our guides.";
      $("#helpful").innerHTML = `<span class="hlp-done">${esc(msg)}</span>`;
    }));
}

$("#form").addEventListener("submit", submit);
