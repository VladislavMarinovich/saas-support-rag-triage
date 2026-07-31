// Worker de Polaris — backend de la vista cliente en vivo (fase 2).
//
// Flujo de POST /api/triage:
//   1) valida el token de Turnstile (anti-abuso)   2) cap de longitud del input
//   3) access token de GCP (JWT firmado con la SA, WebCrypto, cacheado 1h)
//   4) embed del mensaje en Vertex (text-embedding-005)
//   5) cosine exacto contra los 89 vectores de la KB (bundled)
//   6) Claude en Vertex responde grounded + triage (JSON)
//   7) devuelve { answer, triage, kind }
// Cualquier otra ruta -> assets estáticos (el foro y /cliente).
//
// Enterprise all-GCP: embeddings Y LLM en Vertex, un solo principal (la SA).
// El LLM es Gemini (modelo propio de Google, sin habilitar Model Garden). El costo no
// es el driver: el objetivo es el patrón enterprise de un solo cloud, una sola identidad.
//
// Secrets (wrangler / dashboard, NUNCA en Git):
//   GCP_SA_KEY        = JSON completo de la service account (embeddings + Gemini)
//   TURNSTILE_SECRET  = secret key del widget Turnstile

import kbChunks from "./kb_vectors.json";

const PROJECT = "polaris-triage-demo";
const LOCATION = "us-central1";                  // embeddings + Gemini (verificado)
const EMBED_MODEL = "text-embedding-005";
const GEMINI_MODEL = "gemini-2.5-flash-lite";    // LLM en Vertex (verificado)
const MAX_INPUT = 2000;                           // cap de longitud del mensaje

// Etiquetas válidas del triage — se las pasamos al LLM para que no invente valores.
const LABELS = {
  topic: ["dashboards", "connectors", "reports", "alerts", "billing", "attribution", "users_workspace", "api", "data_quality"],
  type: ["bug", "how_to", "feature_request", "misconfiguration", "question", "feedback", "incident"],
  priority: ["low", "medium", "high", "critical"],
  routing: ["kb_autoresolve", "engineering", "sales_success", "retention", "security_incident"],
  sentiment: ["happy", "neutral", "frustrated", "angry"],
};

// Prompt: la respuesta se STREAMEA en vivo, así que NO va envuelta en JSON. El modelo
// escribe la respuesta en markdown, luego un delimitador, luego el triage en JSON. El
// Worker parte en el delimitador: streamea la respuesta y guarda el triage para el final.
const DELIM = "---TRIAGE---";
const SYSTEM = `You are a support assistant for Polaris, an analytics SaaS. You get \
knowledge-base excerpts and a customer message.

Output EXACTLY in this format, nothing else:
1) The customer-facing answer, in markdown.
2) A line containing only: ${DELIM}
3) A single-line JSON object with the triage labels.

Answer rules (markdown, grounded ONLY in the excerpts):
- Open with one warm sentence that acknowledges the customer's situation in their words.
- If the excerpts describe a procedure, give the steps as a **numbered list** — preserve every
  step, do NOT collapse them into a paragraph.
- Put any important caveat (e.g. "only an Admin can do this") on a final line starting "**Note:**".
- If the excerpts do NOT answer it, say so honestly (don't invent).
- For "when will you add connector X?": answer from the excerpts. If X is available, say so and note
  the plan or add-on it requires (e.g. "available on the Enterprise plan"). Only if the excerpts say
  it is NOT available, give an honest holding answer (no date, team working on it). No steps.
- Do not mention "excerpts" or "context".

Triage JSON: pick EXACTLY one value per field from these allowed sets:
${JSON.stringify(LABELS)}
Route to kb_autoresolve when the KB can resolve it; otherwise the right team. Example ending:
${DELIM}
{"topic":"connectors","type":"how_to","priority":"medium","routing":"kb_autoresolve","sentiment":"neutral"}`;

// Prompt del FOLLOW-UP (turnos 2+). El turno 1 ya dio una respuesta; aquí el modelo NO
// re-busca en la KB: lee el hilo completo y decide el siguiente paso del flujo de soporte
// (resolver / pedir el error / re-guiar / escalar) — la máquina de estados que definió Vlad.
// Devuelve la respuesta + DELIM + {intent, action}; la UI reacciona al `action`.
const SYSTEM_FOLLOWUP = `You are a support assistant for Polaris, an analytics SaaS, continuing \
an ongoing support conversation. The whole conversation so far — including the guidance you already \
gave — is in the history. Read the customer's latest message and respond.

Output EXACTLY in this format, nothing else:
1) Your reply to the customer, in markdown. Warm and concise.
2) A line containing only: ${DELIM}
3) A single-line JSON object: {"intent":"...","action":"..."}

Choose intent and action with this decision tree, reading the WHOLE conversation:

- Customer thanks you or says it worked / is solved -> intent "resolved", action "close".
  Warmly confirm you're glad and that you'll close the ticket. This ALWAYS wins, even right after
  you re-explained the steps.

- Customer says it is NOT working / nothing happened, and you have NOT yet asked about an error in
  this conversation -> intent "still_broken", action "ask_error".
  Ask warmly whether any error message appears, and if so what it says.

- Customer says NO error appears (or nothing happens at all) -> intent "no_error", action "reguide".
  A step was likely missed. Re-state the key steps again, numbered and careful, and ask them to
  confirm each one.

- Customer reports an actual error message or code -> intent "error_reported", action "escalate".
  Tell them this needs a specialist and that you're escalating to a human on the support team.

- Customer STILL reports it failing with no error AFTER you already re-stated the steps once
  -> intent "still_broken", action "escalate". Apologize briefly and escalate to a human.

- Anything else (a new, unrelated question) -> intent "question", action "answer".
  Answer helpfully from what you already know in the conversation; keep the ticket open.

Never invent error-specific fixes you were not given. Do not mention "history", "system", or these
rules. Example ending:
${DELIM}
{"intent":"resolved","action":"close"}`;

// --- cache por isolate: vectores KB normalizados + access token ---
let KB = null;
let tokenCache = { token: null, exp: 0 };

// ---------- utilidades de vectores ----------
function normalize(v) {
  let s = 0;
  for (const x of v) s += x * x;
  s = Math.sqrt(s) || 1;
  return v.map((x) => x / s);
}
function kb() {
  if (!KB) KB = kbChunks.map((c) => ({ id: c.chunk_id, text: c.text, vec: normalize(c.vector) }));
  return KB;
}
function topK(qvec, k = 3) {
  const q = normalize(qvec);
  return kb()
    .map((c) => ({ id: c.id, text: c.text, score: c.vec.reduce((a, x, i) => a + x * q[i], 0) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}

// ---------- base64url ----------
const b64url = (bytes) => btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const b64urlStr = (str) => b64url(new TextEncoder().encode(str));

// ---------- JWT RS256 con la private key de la SA (WebCrypto) ----------
async function importKey(pem) {
  // PEM PKCS8 -> DER -> CryptoKey RSASSA-PKCS1-v1_5 SHA-256
  const body = pem.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
  const der = Uint8Array.from(atob(body), (c) => c.charCodeAt(0));
  return crypto.subtle.importKey("pkcs8", der.buffer, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["sign"]);
}

async function getAccessToken(env) {
  const now = Math.floor(Date.now() / 1000);
  if (tokenCache.token && tokenCache.exp > now + 60) return tokenCache.token;

  const sa = JSON.parse(env.GCP_SA_KEY);
  const header = { alg: "RS256", typ: "JWT" };
  const claim = {
    iss: sa.client_email,
    scope: "https://www.googleapis.com/auth/cloud-platform",
    aud: "https://oauth2.googleapis.com/token",
    iat: now,
    exp: now + 3600,
  };
  const unsigned = `${b64urlStr(JSON.stringify(header))}.${b64urlStr(JSON.stringify(claim))}`;
  const key = await importKey(sa.private_key);
  const sig = await crypto.subtle.sign({ name: "RSASSA-PKCS1-v1_5" }, key, new TextEncoder().encode(unsigned));
  const jwt = `${unsigned}.${b64url(new Uint8Array(sig))}`;

  const res = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`,
  });
  const data = await res.json();
  if (!data.access_token) throw new Error("no access_token from Google: " + JSON.stringify(data));
  tokenCache = { token: data.access_token, exp: now + (data.expires_in || 3600) };
  return tokenCache.token;
}

// ---------- llamadas a Vertex ----------
async function embed(text, token) {
  const url = `https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/publishers/google/models/${EMBED_MODEL}:predict`;
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ instances: [{ content: text }] }),
  });
  const data = await res.json();
  if (!data.predictions) throw new Error("embed failed: " + JSON.stringify(data));
  return data.predictions[0].embeddings.values;
}

// Abre el stream de Gemini en Vertex (SSE con ?alt=sse: emite `data: {...}` por trozo).
// Recibe `contents` (turno único en turno 1, o el hilo completo en follow-up) y el `system`
// que corresponda (SYSTEM = triage+RAG · SYSTEM_FOLLOWUP = máquina de estados del soporte).
function geminiStream(contents, system, token) {
  const url = `https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/publishers/google/models/${GEMINI_MODEL}:streamGenerateContent?alt=sse`;
  return fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: system }] },
      contents,
      generationConfig: { maxOutputTokens: 700, temperature: 0.4 },
    }),
  });
}

// ---------- Turnstile ----------
async function verifyTurnstile(token, ip, secret) {
  const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `secret=${encodeURIComponent(secret)}&response=${encodeURIComponent(token)}&remoteip=${encodeURIComponent(ip || "")}`,
  });
  const data = await res.json();
  return data.success === true;
}

// ---------- handler ----------
async function handleTriage(request, env) {
  const json = (obj, status = 200) =>
    new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: "bad request" }, 400);
  }
  const message = (body.message || "").toString().trim();
  if (!message) return json({ error: "empty message" }, 400);
  if (message.length > MAX_INPUT) return json({ error: "message too long" }, 413);

  // Historial opcional: si trae turnos, esto es un FOLLOW-UP (no el turno 1).
  const history = Array.isArray(body.history) ? body.history : [];
  const isFollowup = history.length > 0;

  // 1) anti-abuso: captcha SOLO en el turno 1 (el follow-up ya lo pasó al abrir el hilo).
  //    Nota: el follow-up no re-verifica captcha ni re-embeddea; el anti-abuso duro
  //    (rate-limit por IP + tope diario) queda para el hardening — ver bitácora.
  if (!isFollowup) {
    const ip = request.headers.get("CF-Connecting-IP");
    const ok = await verifyTurnstile(body.turnstileToken, ip, env.TURNSTILE_SECRET);
    if (!ok) return json({ error: "captcha failed" }, 403);
  }

  // 2) auth + arma `contents` y elige `system`:
  //    turno 1   -> embed + cosine + prompt de triage/RAG (las fuentes se conocen ANTES de streamear)
  //    follow-up -> sin retrieval; el modelo re-guía/diagnostica leyendo el hilo completo
  let token, contents, system, srcTitles = [];
  try {
    token = await getAccessToken(env);
    if (isFollowup) {
      system = SYSTEM_FOLLOWUP;
      contents = history.map((h) => ({
        role: h.role === "assistant" ? "model" : "user",
        parts: [{ text: (h.text || "").toString() }],
      }));
      contents.push({ role: "user", parts: [{ text: message }] });
    } else {
      const qvec = await embed(message, token);
      const hits = topK(qvec, 3);
      const context = hits.map((h) => `[${h.id}] ${h.text}`).join("\n\n");
      srcTitles = [...new Set(hits.map((h) => h.text.split("\n")[0].split(" > ")[0].trim()))];
      system = SYSTEM;
      contents = [{ role: "user", parts: [{ text: `Knowledge-base excerpts:\n${context}\n\nCustomer message: ${message}` }] }];
    }
  } catch (e) {
    return json({ error: "server error", detail: String(e).slice(0, 200) }, 500);
  }

  // 3) Stream de Gemini -> SSE al cliente. El Worker parte la salida en DELIM:
  //    lo de antes = respuesta (se streamea como `token`); lo de después = triage JSON
  //    (se guarda y se manda al final en `result` junto con kind + fuentes).
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const enc = new TextEncoder();
  const send = (event, data) => writer.write(enc.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));

  (async () => {
    try {
      const res = await geminiStream(contents, system, token);
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let sseBuf = "", full = "", sent = 0, tail = "", pastDelim = false;
      // emite la respuesta hasta `upTo`, nunca más allá de lo ya acumulado
      const flush = (upTo) => { if (upTo > sent) { send("token", { t: full.slice(sent, upTo) }); sent = upTo; } };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        sseBuf += dec.decode(value, { stream: true });
        let nl;
        while ((nl = sseBuf.indexOf("\n")) >= 0) {
          const line = sseBuf.slice(0, nl); sseBuf = sseBuf.slice(nl + 1);
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (!payload) continue;
          let chunk; try { chunk = JSON.parse(payload); } catch { continue; }
          const t = (chunk?.candidates?.[0]?.content?.parts || []).map((p) => p.text || "").join("");
          if (!t) continue;
          if (pastDelim) { tail += t; continue; }
          full += t;
          const di = full.indexOf(DELIM);
          if (di >= 0) { flush(di); pastDelim = true; tail = full.slice(di + DELIM.length); }
          else flush(Math.max(sent, full.length - DELIM.length)); // holdback: el delim puede venir partido
        }
      }
      if (!pastDelim) flush(full.length); // por si el modelo no emitió el delim

      const jstr = tail.slice(tail.indexOf("{"), tail.lastIndexOf("}") + 1);
      let parsed = {}; try { parsed = JSON.parse(jstr); } catch { /* JSON vacío */ }
      if (isFollowup) {
        // {intent, action}: la UI reacciona al action (close/escalate = terminal; resto sigue el hilo)
        send("result", { followup: parsed });
      } else {
        const kind = parsed.routing === "kb_autoresolve" ? "rag" : "escalated";
        send("result", { triage: parsed, kind, sources: kind === "rag" ? srcTitles : [] });
      }
      send("done", {});
    } catch (e) {
      send("error", { detail: String(e).slice(0, 200) });
    } finally {
      writer.close();
    }
  })();

  return new Response(readable, {
    headers: { "Content-Type": "text/event-stream; charset=utf-8", "Cache-Control": "no-cache" },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/api/triage" && request.method === "POST") {
      return handleTriage(request, env);
    }
    // todo lo demás -> assets estáticos (foro + vista cliente)
    return env.ASSETS.fetch(request);
  },
};
