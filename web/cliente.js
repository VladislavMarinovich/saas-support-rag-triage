// Vista cliente — envía el ticket al Worker y muestra la respuesta en vivo, con HILO MULTI-TURNO.
// Contrato con el Worker:
//   Turno 1:   POST /api/triage { subject, message, turnstileToken }
//              -> SSE: token* + result { triage, kind, sources }
//   Follow-up: POST /api/triage { message, history:[{role,text}...] }   (sin captcha, sin retrieval)
//              -> SSE: token* + result { followup:{ intent, action } }
//
// `action` del follow-up gobierna la UI (máquina de estados de soporte):
//   close    -> ticket resuelto, cierra el composer
//   escalate -> a soporte humano, cierra el composer
//   ask_error / reguide / answer -> sigue el hilo, composer abierto
//
// Modo mock (?mock=1): respuestas canned (turno 1 y follow-ups) para probar la UI sin backend.

const $ = (s) => document.querySelector(s);
const MOCK = new URLSearchParams(location.search).has("mock");

// El hilo completo de la conversación (se manda al Worker en cada follow-up).
// role: "user" | "assistant"  ·  text: mensaje / respuesta (markdown, sin el triage JSON).
const history = [];
let turnSeq = 0; // ids únicos por respuesta para no chocar refs entre turnos

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

// --- respuestas canned para el modo mock ---
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

// Mock del follow-up: replica la máquina de estados sin backend, para probar la UI.
// OJO el orden: "no error" contiene la palabra "error", así que la rama de NEGACIÓN
// (no-error -> re-guiar) se evalúa ANTES que la de error real (-> escalar).
function mockFollowup(message, hist) {
  const m = message.toLowerCase();
  const reguidedBefore = hist.some((h) => h.role === "assistant" && /try again, carefully/i.test(h.text));
  const thanks = /thank|thx|works|worked|solved|resuelto|gracias|funcion/.test(m);
  const notWorking = /not work|doesn'?t|nothing|still|aún|aun|nada|no funciona|isn'?t working/.test(m);
  const noError = /no error|sin error|ningún error|ningun error|no aparece|nothing (happens|appears)/.test(m);
  const realError = /error|code|failed|exception|crash|denied|403|500/.test(m) && !noError;

  // "gracias / funcionó" -> resuelto (SIEMPRE gana, incluso tras re-guiar)
  if (thanks) return { answer: "Awesome — glad that did it! I'll close this ticket for you. 🎉", followup: { intent: "resolved", action: "close" } };
  // ya se re-guió y SIGUE fallando (sin error) -> escalar por fallo repetido
  if (reguidedBefore && (notWorking || noError)) return { answer: "I'm sorry this is still failing. I'm escalating you to a human specialist who can dig deeper.", followup: { intent: "still_broken", action: "escalate" } };
  // respondió que NO sale error -> no completó los pasos -> re-guiar
  if (noError) return { answer: "Let's try again, carefully:\n\n1. Open **Settings > Connectors**.\n2. Click **Reconnect** on the expired connector.\n3. Wait for the next sync.\n\nDid each step work?", followup: { intent: "no_error", action: "reguide" } };
  // reportó un error real -> escalar (futuro: primero la KB de errores)
  if (realError) return { answer: "Thanks for the details. That error needs a specialist — I'm escalating you to a human on our support team now.", followup: { intent: "error_reported", action: "escalate" } };
  // primer "no funciona" -> preguntar por el error
  if (notWorking) return { answer: "Sorry to hear that. Does any **error message** appear on screen? If so, what does it say?", followup: { intent: "still_broken", action: "ask_error" } };
  // otra cosa -> pedir un poco más de contexto, hilo abierto
  return { answer: "Happy to help further. Could you tell me a bit more about what you're seeing?", followup: { intent: "question", action: "answer" } };
}

// --- streaming compartido: corre el typewriter dentro de refs.body y consume el SSE ---
// Devuelve { full, result }. `full` = texto de la respuesta (markdown, sin triage/JSON).
async function runStream(refs, payload) {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const CPS = reduce ? 1e6 : 190;      // velocidad de revelado (chars/segundo)
  let full = "", streaming = true, start = null;
  const render = (text) => {
    const typing = streaming || text.length < full.length;
    refs.body.innerHTML = mdToHtml(text) + (typing ? '<span class="cursor"></span>' : "");
    refs.body.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };
  // Revela por TIEMPO transcurrido (robusto al throttling de setInterval en tabs de fondo).
  const typewriter = new Promise((resolve) => {
    const id = setInterval(() => {
      if (!full.length) return;
      if (start === null) start = performance.now();
      const want = Math.floor(((performance.now() - start) / 1000) * CPS);
      render(full.slice(0, Math.min(want, full.length)));
      if (want >= full.length && !streaming) { clearInterval(id); resolve(); }
    }, 30);
  });

  let result = null;
  try {
    if (MOCK) {
      const m = payload.history ? mockFollowup(payload.message, payload.history) : mockResponse(payload.message);
      full = m.answer;                 // el typewriter lo pacea por tiempo
      result = m;
    } else {
      const res = await fetch("/api/triage", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      let streamErr = null;
      await readSSE(res, (event, data) => {
        if (event === "token") full += (data.t || "");
        else if (event === "result") result = data;
        else if (event === "error") streamErr = data.detail || "stream error";
      });
      if (streamErr) throw new Error(streamErr);
    }
    streaming = false;
    await typewriter;                  // espera a revelar TODO el texto
    return { full, result: result || {} };
  } catch (e) {
    streaming = false;                 // deja que el intervalo del typewriter se detenga
    throw e;
  }
}

// --- envío del turno 1 ---
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

  history.length = 0;                              // hilo nuevo
  const refs = buildSkeleton({ subject, message }); // arma el hilo con el post del cliente + skeleton

  try {
    const { full, result } = await runStream(refs, { subject, message, turnstileToken: token });
    finalizeReply(refs, result, full);
    history.push({ role: "user", text: message }, { role: "assistant", text: full });
    mountComposer();                              // habilita follow-ups
  } catch (e) {
    $("#answer").hidden = true;
    $("#err").textContent = "Sorry, something went wrong. Please try again.";
    if (window.turnstile) turnstile.reset();
  } finally {
    btn.disabled = false; btn.textContent = "Send message";
  }
}

// --- envío de un follow-up (turnos 2+) ---
async function sendFollowup(text) {
  const refs = appendTurn(text);                  // añade el post del cliente + skeleton de respuesta
  setComposerDisabled(true);
  try {
    const { full, result } = await runStream(refs, { message: text, history: history.slice() });
    const action = (result.followup && result.followup.action) || "answer";
    finalizeFollowup(refs, full, action);
    history.push({ role: "user", text }, { role: "assistant", text: full });
    if (action === "close" || action === "escalate") removeComposer(action);
    else setComposerDisabled(false);
  } catch (e) {
    refs.body.innerHTML = '<p class="err-inline">Sorry, something went wrong. Please try again.</p>';
    setComposerDisabled(false);
  }
}

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

// --- construcción del hilo (DOM) ---
// Un "post" del cliente (op). title opcional (solo el turno 1 lo usa, con el asunto).
function opPost(title, bodyText) {
  const el = document.createElement("div");
  el.className = "post op";
  el.innerHTML = `
    <div class="post-head"><span class="who">You</span><span class="dot">·</span><span class="when">just now</span></div>
    ${title ? `<div class="post-title">${esc(title)}</div>` : ""}
    <div class="post-body">${esc(bodyText)}</div>`;
  return el;
}

// Un "post" de respuesta (reply) con skeleton; devuelve el elemento + refs a sus partes.
function replyPost() {
  const id = ++turnSeq;
  const el = document.createElement("div");
  el.className = "post reply";
  el.innerHTML = `
    <div class="post-head"><span class="verified" data-v="${id}">Polaris AI is typing…</span></div>
    <div class="response-body" data-b="${id}"></div>
    <div data-m="${id}"></div>`;
  return { el, refs: { body: el.querySelector(`[data-b="${id}"]`), meta: el.querySelector(`[data-m="${id}"]`), verified: el.querySelector(`[data-v="${id}"]`) } };
}

// Turno 1: crea el hilo con el post original del cliente + el primer skeleton de respuesta.
function buildSkeleton(asked) {
  const title = (asked.subject && asked.subject.trim()) || asked.message.slice(0, 60);
  turnSeq = 0;
  $("#answer").hidden = false;
  $("#answer").innerHTML = `<div class="thread" id="thread"></div>`;
  const thread = $("#thread");
  thread.appendChild(opPost(title, asked.message));
  const { el, refs } = replyPost();
  thread.appendChild(el);
  return refs;
}

// Follow-up: añade el post del cliente + un nuevo skeleton de respuesta al hilo existente.
function appendTurn(userText) {
  const thread = $("#thread");
  thread.appendChild(opPost(null, userText));
  const { el, refs } = replyPost();
  thread.appendChild(el);
  refs.body.scrollIntoView({ behavior: "smooth", block: "nearest" });
  return refs;
}

// --- cierre de la respuesta del TURNO 1: badge + fuentes + utilidad + triage colapsable ---
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

// --- cierre de la respuesta de un FOLLOW-UP: badge según el action de la máquina de estados ---
function finalizeFollowup(refs, answerText, action) {
  refs.body.innerHTML = mdToHtml(answerText);
  const badge = {
    close: "✓ Resolved — ticket closed",
    escalate: "↗ Escalated to human support",
  }[action] || "✓ Polaris AI";
  refs.verified.textContent = badge;
  refs.verified.classList.toggle("escalated", action === "escalate");
  refs.verified.classList.toggle("resolved", action === "close");
}

// --- composer de follow-ups (aparece tras la primera respuesta; se retira al cerrar/escalar) ---
function mountComposer() {
  if ($("#composer")) return;
  const box = document.createElement("form");
  box.id = "composer";
  box.className = "composer";
  box.innerHTML = `
    <textarea id="reply" rows="2" maxlength="2000"
      placeholder="Reply to continue… (e.g. &ldquo;thanks, that worked&rdquo; or &ldquo;still not working&rdquo;)"></textarea>
    <button type="submit" id="replybtn">Reply</button>`;
  $("#answer").appendChild(box);
  box.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const t = $("#reply").value.trim();
    if (!t) return;
    $("#reply").value = "";
    sendFollowup(t);
  });
}
function setComposerDisabled(d) {
  const r = $("#reply"), b = $("#replybtn");
  if (r) r.disabled = d;
  if (b) { b.disabled = d; b.textContent = d ? "Sending…" : "Reply"; }
}
function removeComposer(action) {
  const c = $("#composer"); if (c) c.remove();
  const note = document.createElement("div");
  note.className = "thread-end " + (action === "escalate" ? "escalated" : "resolved");
  note.textContent = action === "escalate"
    ? "This conversation has been handed to a human support specialist."
    : "This ticket is resolved. Thanks for using Polaris support!";
  $("#answer").appendChild(note);
}

$("#form").addEventListener("submit", submit);
