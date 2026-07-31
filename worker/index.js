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
function geminiStream(context, message, token) {
  const url = `https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/publishers/google/models/${GEMINI_MODEL}:streamGenerateContent?alt=sse`;
  const user = `Knowledge-base excerpts:\n${context}\n\nCustomer message: ${message}`;
  return fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: SYSTEM }] },
      contents: [{ role: "user", parts: [{ text: user }] }],
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

  // 1) anti-abuso: captcha
  const ip = request.headers.get("CF-Connecting-IP");
  const ok = await verifyTurnstile(body.turnstileToken, ip, env.TURNSTILE_SECRET);
  if (!ok) return json({ error: "captcha failed" }, 403);

  // 2) auth + embed + retrieve (las fuentes se conocen ANTES de streamear)
  let token, hits, context;
  try {
    token = await getAccessToken(env);
    const qvec = await embed(message, token);
    hits = topK(qvec, 3);
    context = hits.map((h) => `[${h.id}] ${h.text}`).join("\n\n");
  } catch (e) {
    return json({ error: "server error", detail: String(e).slice(0, 200) }, 500);
  }
  const srcTitles = [...new Set(hits.map((h) => h.text.split("\n")[0].split(" > ")[0].trim()))];

  // 3) Stream de Gemini -> SSE al cliente. El Worker parte la salida en DELIM:
  //    lo de antes = respuesta (se streamea como `token`); lo de después = triage JSON
  //    (se guarda y se manda al final en `result` junto con kind + fuentes).
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const enc = new TextEncoder();
  const send = (event, data) => writer.write(enc.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));

  (async () => {
    try {
      const res = await geminiStream(context, message, token);
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
      let triage = {}; try { triage = JSON.parse(jstr); } catch { /* triage vacío */ }
      const kind = triage.routing === "kb_autoresolve" ? "rag" : "escalated";
      send("result", { triage, kind, sources: kind === "rag" ? srcTitles : [] });
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
