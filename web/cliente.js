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
  try {
    let data;
    if (MOCK) {
      await new Promise((r) => setTimeout(r, 500)); // simula latencia
      data = mockResponse(message);
    } else {
      const res = await fetch("/api/triage", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject, message, turnstileToken: token }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
    }
    renderAnswer(data);
  } catch (e) {
    $("#err").textContent = "Sorry, something went wrong. Please try again.";
    if (window.turnstile) turnstile.reset();
  } finally {
    btn.disabled = false; btn.textContent = "Send message";
  }
}

// --- render de la respuesta ---
function renderAnswer(data) {
  const isRag = data.kind === "rag";
  const t = data.triage || {};
  const labels = [["topic", t.topic], ["type", t.type], ["priority", t.priority], ["routing", t.routing]]
    .filter(([, v]) => v);
  $("#answer").hidden = false;
  $("#answer").innerHTML = `
    <div class="answer-head">
      <span class="answer-kind">${isRag ? "◆ Answered from our knowledge base" : "↗ Routed to a specialist"}</span>
    </div>
    <div class="response"><div class="response-body">${mdToHtml(data.answer || "")}</div></div>
    <div class="triage-line">Categorized as:
      ${labels.map(([k, v]) => `<strong>${esc(pretty(v))}</strong> <span style="opacity:.6">(${esc(k)})</span>`).join(" · ")}
    </div>`;
  $("#answer").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

$("#form").addEventListener("submit", submit);
