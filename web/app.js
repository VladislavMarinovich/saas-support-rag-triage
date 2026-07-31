// Foro Polaris — vanilla JS. Carga el export estático y arma lista + filtros + detalle.
// Sin framework ni build step: se sirve tal cual desde Cloudflare Pages.

const state = { all: [], filtered: [], selected: null, page: 0, perPage: 25 };

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const TITLE = (t) => (t.subject && t.subject.trim()) || t.body.slice(0, 60);
const pretty = (s) => String(s ?? "").replace(/_/g, " ");
const fmtDate = (iso) => (iso || "").slice(0, 10);

// Mini-render de markdown → HTML. El LLM devuelve **negrita**, listas y párrafos;
// sin esto se ven los asteriscos crudos. SEGURO: escapamos TODO primero (esc), así
// el contenido no puede inyectar HTML; luego solo introducimos nuestras propias
// etiquetas controladas para negrita/código/listas/párrafos.
// El orden importa: links primero, luego negrita (**) ANTES que itálica (*), luego
// código. `s` ya viene HTML-escapado; solo linkeamos http(s)/mailto (nunca javascript:).
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
    const ol = t.match(/^\d+\.\s+(.*)/);      // "1. paso"
    const ul = t.match(/^[-*]\s+(.*)/);        // "- item" / "* item"
    if (ol) {
      if (list !== "ol") { closeList(); html += "<ol>"; list = "ol"; }
      html += `<li>${mdInline(ol[1])}</li>`;
    } else if (ul) {
      if (list !== "ul") { closeList(); html += "<ul>"; list = "ul"; }
      html += `<li>${mdInline(ul[1])}</li>`;
    } else if (!t) {
      closeList();                             // línea en blanco: cierra la lista
    } else {
      closeList();
      html += `<p>${mdInline(t)}</p>`;
    }
  }
  closeList();
  return html;
}

// ---- carga ----
async function load() {
  try {
    const res = await fetch("data/tickets.json");
    if (!res.ok) throw new Error(res.status);
    state.all = await res.json();
  } catch (e) {
    $("#list").innerHTML = `<li class="ticket">No pude cargar data/tickets.json (${esc(e.message)}).</li>`;
    return;
  }
  // Tickets EN VIVO capturados por /cliente (persistidos en D1). Se anteponen con badge "Live".
  // Si el foro se sirve estático (sin Worker) el fetch falla -> solo se ven los sintéticos.
  try {
    const r = await fetch("/api/tickets");
    if (r.ok) {
      const { tickets } = await r.json();
      const live = (tickets || []).map(toForoShape).filter(Boolean);
      state.all = [...live, ...state.all];
    }
  } catch { /* modo estático: sin tickets en vivo */ }
  buildFilters();
  renderStats();
  apply();
}

// Mapea un ticket de D1 {ticket_id, created, subject, thread(JSON), triage(JSON), status}
// a la MISMA forma que renderiza el foro (la de tickets.json).
function toForoShape(t) {
  let thread = [], triage = {};
  try { thread = JSON.parse(t.thread) || []; } catch { /* thread inválido */ }
  try { triage = JSON.parse(t.triage) || {}; } catch { /* triage vacío */ }
  const firstUser = thread.find((x) => x.role === "user");
  const firstBot = thread.find((x) => x.role === "assistant");
  const routing = triage.routing || (t.status === "escalated" ? "escalated" : "kb_autoresolve");
  return {
    ticket_id: t.ticket_id,
    created_at: new Date(t.created).toISOString(),
    channel: "web", plan: "", user_role: "",
    reported_category: "",
    topic: triage.topic || "", type: triage.type || "",
    priority: triage.priority || "", routing,
    sentiment: triage.sentiment || "",
    event_id: null, event_type: null,
    subject: t.subject || "",
    body: firstUser ? firstUser.text : "",
    response: firstBot ? firstBot.text : "",
    response_kind: routing === "kb_autoresolve" ? "rag" : "escalated",
    live: true,
    status: t.status,
  };
}

// ---- filtros (opciones únicas desde los datos) ----
function buildFilters() {
  const uniq = (k) => [...new Set(state.all.map((t) => t[k]).filter(Boolean))].sort();
  fillSelect("#f-routing", uniq("routing"), pretty);
  fillSelect("#f-type", uniq("type"), pretty);
  fillSelect("#f-priority", ["critical", "high", "medium", "low"].filter(
    (p) => state.all.some((t) => t.priority === p)));
  fillSelect("#f-topic", uniq("topic"), pretty);
  // meses presentes en la data (YYYY-MM), siempre en orden cronológico
  const months = [...new Set(state.all.map((t) => (t.created_at || "").slice(0, 7)).filter(Boolean))].sort();
  fillSelect("#f-month", months);
  // cualquier cambio de filtro/orden vuelve a la página 1
  ["#search", "#f-routing", "#f-type", "#f-priority", "#f-topic", "#f-month", "#f-kind", "#sort"]
    .forEach((sel) => $(sel).addEventListener("input", () => { state.page = 0; apply(); }));
}
function fillSelect(sel, values, label = (x) => x) {
  const el = $(sel);
  values.forEach((v) => {
    const o = document.createElement("option");
    o.value = v; o.textContent = label(v);
    el.appendChild(o);
  });
}

// ---- métricas ----
function renderStats() {
  const n = state.all.length;
  const kb = state.all.filter((t) => t.routing === "kb_autoresolve").length;
  const events = state.all.filter((t) => t.event_id).length;
  const stats = [
    ["Tickets", n.toLocaleString()],
    ["Auto-resolved from KB", n ? Math.round((kb / n) * 100) + "%" : "—"],
    ["Escalated", (n - kb).toLocaleString()],
    ["From an event spike", events.toLocaleString()],
  ];
  $("#stats").innerHTML = stats.map(([lbl, num]) =>
    `<div class="stat"><div class="num">${esc(num)}</div><div class="lbl">${esc(lbl)}</div></div>`).join("");
}

// ---- aplicar filtros + búsqueda + orden ----
function apply() {
  const q = $("#search").value.trim().toLowerCase();
  const fr = $("#f-routing").value, fp = $("#f-priority").value;
  const fty = $("#f-type").value, fto = $("#f-topic").value;
  const fm = $("#f-month").value, fk = $("#f-kind").value;
  state.filtered = state.all.filter((t) =>
    (!fr || t.routing === fr) && (!fty || t.type === fty) &&
    (!fp || t.priority === fp) && (!fto || t.topic === fto) &&
    (!fm || (t.created_at || "").startsWith(fm)) && (!fk || t.response_kind === fk) &&
    (!q || (t.body + " " + (t.subject || "")).toLowerCase().includes(q)));

  // ordenar por fecha según el toggle (desc = más nueva primero)
  const dir = $("#sort").value === "asc" ? 1 : -1;
  state.filtered.sort((a, b) =>
    dir * String(a.created_at).localeCompare(String(b.created_at)));
  renderList();
}

// ---- lista (paginada) ----
function renderList() {
  const list = $("#list");
  const total = state.filtered.length;
  const pages = Math.max(1, Math.ceil(total / state.perPage));
  state.page = Math.min(state.page, pages - 1);           // clamp por si el filtro achicó
  const start = state.page * state.perPage;
  const pageItems = state.filtered.slice(start, start + state.perPage);

  $("#count").textContent = `${total} ticket${total === 1 ? "" : "s"}`;

  // data-i = índice GLOBAL en state.filtered (no el de la página), para seleccionar bien
  list.innerHTML = pageItems.map((t, i) => `
    <li class="ticket ${state.selected === t.ticket_id ? "active" : ""}" data-i="${start + i}">
      <div class="row1">
        ${t.live ? `<span class="badge live">● Live</span>` : ""}
        <span class="badge route-${esc(t.routing)}">${esc(pretty(t.routing))}</span>
        <span class="badge prio-${esc(t.priority)}">${esc(t.priority)}</span>
        ${t.event_id ? `<span class="badge event">${esc(t.event_type)}</span>` : ""}
        <span class="tid">${esc(t.ticket_id)} · ${esc(fmtDate(t.created_at))}</span>
      </div>
      <div class="snippet">${esc(TITLE(t))}</div>
    </li>`).join("");

  list.querySelectorAll(".ticket").forEach((el) =>
    el.addEventListener("click", () => select(state.filtered[+el.dataset.i])));

  renderPager(pages);
}

// ---- controles de paginación ----
function renderPager(pages) {
  const pager = $("#pager");
  if (pages <= 1) { pager.innerHTML = ""; return; }
  pager.innerHTML = `
    <button id="prev" ${state.page === 0 ? "disabled" : ""}>← Prev</button>
    <span class="page-ind">Page ${state.page + 1} of ${pages}</span>
    <button id="next" ${state.page >= pages - 1 ? "disabled" : ""}>Next →</button>`;
  $("#prev").onclick = () => { if (state.page > 0) { state.page--; renderList(); $("#list").scrollTop = 0; } };
  $("#next").onclick = () => { if (state.page < pages - 1) { state.page++; renderList(); $("#list").scrollTop = 0; } };
}

// ---- detalle ----
function select(t) {
  state.selected = t.ticket_id;
  renderList();
  const isRag = t.response_kind === "rag";
  const labels = [
    ["topic", t.topic], ["type", t.type], ["priority", t.priority],
    ["routing", t.routing], ["sentiment", t.sentiment],
  ];
  $("#detail").innerHTML = `
    <h2>${t.live ? `<span class="badge live">● Live</span> ` : ""}${esc(TITLE(t))}</h2>
    <div class="meta">${esc(t.ticket_id)} · ${esc(fmtDate(t.created_at))} · ${esc(t.channel)}${
      t.live ? ` · <b>${esc(t.status || "open")}</b>` : ` · ${esc(pretty(t.plan))} plan · ${esc(pretty(t.user_role))}`}</div>

    <div class="section-label">Customer message</div>
    <div class="body-text">${esc(t.body)}</div>

    <div class="section-label">Triage (model-predicted)</div>
    <div class="labels">${labels.map(([k, v]) =>
      `<span class="chip"><b>${esc(k)}:</b> ${esc(pretty(v))}</span>`).join("")}</div>

    <div class="section-label">Response</div>
    <div class="response">
      <div class="response-kind">${isRag ? "◆ Answered from the knowledge base (RAG)" : "↗ Escalation acknowledgement (templated)"}</div>
      <div class="response-body">${mdToHtml(t.response)}</div>
    </div>`;
}

load();
