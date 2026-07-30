// Foro Polaris — vanilla JS. Carga el export estático y arma lista + filtros + detalle.
// Sin framework ni build step: se sirve tal cual desde Cloudflare Pages.

const state = { all: [], filtered: [], selected: null };

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const TITLE = (t) => (t.subject && t.subject.trim()) || t.body.slice(0, 60);
const pretty = (s) => String(s ?? "").replace(/_/g, " ");
const fmtDate = (iso) => (iso || "").slice(0, 10);

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
  buildFilters();
  renderStats();
  apply();
}

// ---- filtros (opciones únicas desde los datos) ----
function buildFilters() {
  const uniq = (k) => [...new Set(state.all.map((t) => t[k]).filter(Boolean))].sort();
  fillSelect("#f-routing", uniq("routing"), pretty);
  fillSelect("#f-priority", ["critical", "high", "medium", "low"].filter(
    (p) => state.all.some((t) => t.priority === p)));
  fillSelect("#f-topic", uniq("topic"), pretty);
  ["#search", "#f-routing", "#f-priority", "#f-topic", "#f-kind"].forEach((sel) =>
    $(sel).addEventListener("input", apply));
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

// ---- aplicar filtros + búsqueda ----
function apply() {
  const q = $("#search").value.trim().toLowerCase();
  const fr = $("#f-routing").value, fp = $("#f-priority").value;
  const ft = $("#f-topic").value, fk = $("#f-kind").value;
  state.filtered = state.all.filter((t) =>
    (!fr || t.routing === fr) && (!fp || t.priority === fp) &&
    (!ft || t.topic === ft) && (!fk || t.response_kind === fk) &&
    (!q || (t.body + " " + (t.subject || "")).toLowerCase().includes(q)));
  renderList();
}

// ---- lista ----
function renderList() {
  const list = $("#list");
  $("#count").textContent = `${state.filtered.length} ticket${state.filtered.length === 1 ? "" : "s"}`;

  list.innerHTML = state.filtered.slice(0, 400).map((t, i) => `
    <li class="ticket ${state.selected === t.ticket_id ? "active" : ""}" data-i="${i}">
      <div class="row1">
        <span class="badge route-${esc(t.routing)}">${esc(pretty(t.routing))}</span>
        <span class="badge prio-${esc(t.priority)}">${esc(t.priority)}</span>
        ${t.event_id ? `<span class="badge event">${esc(t.event_type)}</span>` : ""}
        <span class="tid">${esc(t.ticket_id)} · ${esc(fmtDate(t.created_at))}</span>
      </div>
      <div class="snippet">${esc(TITLE(t))}</div>
    </li>`).join("");

  list.querySelectorAll(".ticket").forEach((el) =>
    el.addEventListener("click", () => select(state.filtered[+el.dataset.i])));
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
    <h2>${esc(TITLE(t))}</h2>
    <div class="meta">${esc(t.ticket_id)} · ${esc(fmtDate(t.created_at))} · ${esc(t.channel)} ·
      ${esc(pretty(t.plan))} plan · ${esc(pretty(t.user_role))}</div>

    <div class="section-label">Customer message</div>
    <div class="body-text">${esc(t.body)}</div>

    <div class="section-label">Triage (model-predicted)</div>
    <div class="labels">${labels.map(([k, v]) =>
      `<span class="chip"><b>${esc(k)}:</b> ${esc(pretty(v))}</span>`).join("")}</div>

    <div class="section-label">Response</div>
    <div class="response">
      <div class="response-kind">${isRag ? "◆ Answered from the knowledge base (RAG)" : "↗ Escalation acknowledgement (templated)"}</div>
      ${esc(t.response)}
    </div>`;
}

load();
