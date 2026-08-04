// Vista cliente — CHAT DE BURBUJAS multi-turno. Envía cada mensaje al Worker y
// revela la respuesta en vivo (streaming). El backend NO cambia.
// Contrato con el Worker:
//   Turno 1:   POST /api/triage { subject, message, turnstileToken }
//              -> SSE: token* + result { triage, kind, sources, ticketId }
//   Follow-up: POST /api/triage { message, history:[{role,text}...], ticketId }  (sin captcha)
//              -> SSE: token* + result { followup:{ intent, action } }
//
// `action` del follow-up gobierna la UI (máquina de estados de soporte):
//   close    -> ticket resuelto, cierra el chat
//   escalate -> a soporte humano, cierra el chat
//   ask_error / reguide / answer -> sigue el hilo
//
// Modo mock (?mock=1): respuestas canned (turno 1 y follow-ups) para probar la UI sin backend.

const $ = (s) => document.querySelector(s);
const MOCK = new URLSearchParams(location.search).has("mock");

const history = [];       // hilo completo: {role:"user"|"assistant", text}
let turnSeq = 0;          // ids únicos por respuesta
let ticketId = null;      // id de la conversación (lo genera el server en el turno 1)
let threadEnded = false;  // true tras close/escalate: el composer queda inhabilitado

// --- helpers de render (mini-markdown seguro) ---
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

// Mock del follow-up: replica la máquina de estados sin backend.
function mockFollowup(message, hist) {
  const m = message.toLowerCase();
  const reguidedBefore = hist.some((h) => h.role === "assistant" && /try again, carefully/i.test(h.text));
  const thanks = /thank|thx|works|worked|solved|resuelto|gracias|funcion/.test(m);
  const notWorking = /not work|doesn'?t|nothing|still|aún|aun|nada|no funciona|isn'?t working/.test(m);
  const noError = /no error|sin error|ningún error|ningun error|no aparece|nothing (happens|appears)/.test(m);
  const realError = /error|code|failed|exception|crash|denied|403|500/.test(m) && !noError;

  if (thanks) return { answer: "Awesome — glad that did it! I'll close this ticket for you. 🎉", followup: { intent: "resolved", action: "close" } };
  if (reguidedBefore && (notWorking || noError)) return { answer: "I'm sorry this is still failing. I'm escalating you to a human specialist who can dig deeper.", followup: { intent: "still_broken", action: "escalate" } };
  if (noError) return { answer: "Let's try again, carefully:\n\n1. Open **Settings > Connectors**.\n2. Click **Reconnect** on the expired connector.\n3. Wait for the next sync.\n\nDid each step work?", followup: { intent: "no_error", action: "reguide" } };
  if (realError) return { answer: "Thanks for the details. That error needs a specialist — I'm escalating you to a human on our support team now.", followup: { intent: "error_reported", action: "escalate" } };
  if (notWorking) return { answer: "Sorry to hear that. Does any **error message** appear on screen? If so, what does it say?", followup: { intent: "still_broken", action: "ask_error" } };
  return { answer: "Happy to help further. Could you tell me a bit more about what you're seeing?", followup: { intent: "question", action: "answer" } };
}

// --- streaming compartido: typewriter dentro de refs.body + consumo del SSE ---
async function runStream(refs, payload) {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const CPS = reduce ? 1e6 : 190;
  let full = "", streaming = true, start = null;
  const render = (text) => {
    const typing = streaming || text.length < full.length;
    refs.body.innerHTML = mdToHtml(text) + (typing ? '<span class="cursor"></span>' : "");
    scrollDown();
  };
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
      await new Promise((r) => setTimeout(r, 450)); // simula latencia
      const m = payload.history ? mockFollowup(payload.message, payload.history) : mockResponse(payload.message);
      full = m.answer;
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
    await typewriter;
    return { full, result: result || {} };
  } catch (e) {
    streaming = false;
    throw e;
  }
}

// Lee un stream SSE y llama onEvent(event, obj) por bloque (\n\n).
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
      if (data) { try { onEvent(event, JSON.parse(data)); } catch { /* bloque parcial */ } }
    }
  }
}

// --- burbujas (DOM) ---
const thread = $("#thread");
const scrollDown = () => { thread.scrollTop = thread.scrollHeight; };

// Burbuja del usuario (derecha).
function userBubble(text) {
  const el = document.createElement("div");
  el.className = "msg user";
  el.innerHTML = `<div class="bubble">${esc(text)}</div>`;
  thread.appendChild(el);
}

// Burbuja de la IA con skeleton; devuelve refs a body/meta/verified.
function aiBubble() {
  const id = ++turnSeq;
  const el = document.createElement("div");
  el.className = "msg ai";
  el.innerHTML = `
    <span class="avatar">P</span>
    <div class="bubble">
      <div class="post-head"><span class="verified" data-v="${id}">Polaris AI is typing…</span></div>
      <div class="response-body" data-b="${id}"></div>
      <div data-m="${id}"></div>
    </div>`;
  thread.appendChild(el);
  return { body: el.querySelector(`[data-b="${id}"]`), meta: el.querySelector(`[data-m="${id}"]`), verified: el.querySelector(`[data-v="${id}"]`) };
}

// Añade el turno (burbuja usuario + skeleton IA) y devuelve refs de la respuesta.
function pushTurn(text) {
  userBubble(text);
  const refs = aiBubble();
  scrollDown();
  return refs;
}

// --- cierre de la respuesta del TURNO 1: badge + fuentes + utilidad + triage colapsable ---
function finalizeReply(refs, data, answerText) {
  const isRag = data.kind === "rag";
  const t = data.triage || {};
  const team = pretty(t.routing || "the right team");
  const humanTeam = t.routing && t.routing !== "kb_autoresolve" ? pretty(t.routing) : "support";
  const labels = [["topic", t.topic], ["type", t.type], ["priority", t.priority], ["routing", t.routing]]
    .filter(([, v]) => v);
  const sources = data.sources || [];

  refs.body.innerHTML = mdToHtml(answerText);
  refs.verified.textContent = isRag ? "✓ Answered by Polaris AI" : "↗ Routed to " + team;

  refs.meta.innerHTML = `
    ${sources.length ? `<div class="sources"><span class="src-lbl">Sources</span>${
      sources.map((s) => `<span class="src-badge">${esc(s)}</span>`).join("")}</div>` : ""}
    <div class="helpful" id="helpful">
      <span class="hlp-q">Was this helpful?</span>
      <button class="hlp-btn" data-v="yes" type="button">Yes</button>
      <button class="hlp-btn" data-v="no" type="button">No</button>
      <button class="hlp-btn human" data-v="human" type="button">Request a human agent</button>
    </div>
    ${labels.length ? `<details class="triage-fold"><summary>How Polaris classified this</summary>
      <div class="labels">${labels.map(([k, v]) =>
        `<span class="chip"><b>${esc(k)}</b> ${esc(pretty(v))}</span>`).join("")}</div>
    </details>` : ""}`;

  refs.meta.querySelectorAll(".hlp-btn").forEach((b) =>
    b.addEventListener("click", () => {
      const v = b.dataset.v;
      const msg = v === "human"
        ? `Got it — we've routed this to our ${humanTeam} team. A specialist will follow up.`
        : v === "yes" ? "Thanks — glad that helped! 🎉" : "Thanks for the feedback — we'll use it to improve our guides.";
      refs.meta.querySelector("#helpful").innerHTML = `<span class="hlp-done">${esc(msg)}</span>`;
    }));
  scrollDown();
}

// --- cierre de la respuesta de un FOLLOW-UP: badge según el action ---
function finalizeFollowup(refs, answerText, action) {
  refs.body.innerHTML = mdToHtml(answerText);
  const badge = {
    close: "✓ Resolved — ticket closed",
    escalate: "↗ Escalated to human support",
  }[action] || "✓ Polaris AI";
  refs.verified.textContent = badge;
  refs.verified.classList.toggle("escalated", action === "escalate");
  refs.verified.classList.toggle("resolved", action === "close");
  scrollDown();
}

// Nota de cierre del hilo (resuelto / escalado) + inhabilita el composer.
function endThread(action) {
  threadEnded = true;
  const note = document.createElement("div");
  note.className = "thread-end " + (action === "escalate" ? "escalated" : "resolved");
  note.textContent = action === "escalate"
    ? "This conversation has been handed to a human support specialist."
    : "This ticket is resolved. Thanks for using Polaris support!";
  thread.appendChild(note);
  const inp = $("#input"), snd = $("#send");
  inp.disabled = true; snd.disabled = true;
  inp.placeholder = "Conversation closed";
  scrollDown();
}

// --- composer ---
const input = $("#input");
const sendBtn = $("#send");

function setBusy(d) {
  input.disabled = d; sendBtn.disabled = d;
  sendBtn.textContent = d ? "…" : "➤";
}
function hideTurnstile() { const ts = $("#ts"); if (ts) ts.style.display = "none"; }

// autosize del textarea
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 128) + "px";
});
// Enter envía; Shift+Enter salta línea
input.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); $("#composer").requestSubmit(); }
});

async function onSubmit(ev) {
  ev.preventDefault();
  if (threadEnded) return;
  const text = input.value.trim();
  $("#err").textContent = "";
  if (!text) return;

  const first = history.length === 0;
  let token = null;
  if (first && !MOCK) {
    token = window.turnstile && turnstile.getResponse();
    if (!token) { $("#err").textContent = "Please complete the verification below."; return; }
  }

  input.value = ""; input.style.height = "auto";
  setBusy(true);
  const refs = pushTurn(text);

  try {
    const payload = first
      ? { subject: "", message: text, turnstileToken: MOCK ? "mock" : token }
      : { message: text, history: history.slice(), ticketId };
    const { full, result } = await runStream(refs, payload);

    if (first) {
      finalizeReply(refs, result, full);
      ticketId = result.ticketId || null;
      hideTurnstile();
    } else {
      const action = (result.followup && result.followup.action) || "answer";
      finalizeFollowup(refs, full, action);
      if (action === "close" || action === "escalate") endThread(action);
    }
    history.push({ role: "user", text }, { role: "assistant", text: full });
  } catch (e) {
    refs.body.innerHTML = '<p class="err-inline">Sorry, something went wrong. Please try again.</p>';
    refs.verified.textContent = "⚠ Error";
    if (first && window.turnstile) turnstile.reset();
  } finally {
    if (!threadEnded) { setBusy(false); input.focus(); }
  }
}

$("#composer").addEventListener("submit", onSubmit);
