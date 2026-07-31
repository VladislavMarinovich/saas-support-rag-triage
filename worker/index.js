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

// Etiquetas válidas del triage — se las pasamos a Claude para que no invente valores.
const LABELS = {
  topic: ["dashboards", "connectors", "reports", "alerts", "billing", "attribution", "users_workspace", "api", "data_quality"],
  type: ["bug", "how_to", "feature_request", "misconfiguration", "question", "feedback", "incident"],
  priority: ["low", "medium", "high", "critical"],
  routing: ["kb_autoresolve", "engineering", "sales_success", "retention", "security_incident"],
  sentiment: ["happy", "neutral", "frustrated", "angry"],
};

// Prompt: respuesta grounded en la KB (o rechazo honesto) + triage estructurado.
const SYSTEM = `You are a support assistant for Polaris, an analytics SaaS. You get \
knowledge-base excerpts and a customer message. Return ONLY a JSON object, no prose around it:
{"answer": string, "triage": {"topic","type","priority","routing","sentiment"}}
Rules for "answer":
- If the excerpts answer the question, reply concisely and helpfully, grounded ONLY in them.
- If they do NOT answer it, say so honestly (don't invent). For "when will you add X?" give an
  honest holding answer (no date, team is working on it).
- Do not mention "excerpts" or "context".
Rules for "triage": pick EXACTLY one value per field from these allowed sets:
${JSON.stringify(LABELS)}
Route to kb_autoresolve when the KB can resolve it; otherwise the right team.`;

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

async function askGemini(context, message, token) {
  const url = `https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/publishers/google/models/${GEMINI_MODEL}:generateContent`;
  const user = `Knowledge-base excerpts:\n${context}\n\nCustomer message: ${message}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: SYSTEM }] },
      contents: [{ role: "user", parts: [{ text: user }] }],
      // responseMimeType fuerza JSON válido -> no hay que parsear prosa
      generationConfig: { maxOutputTokens: 700, responseMimeType: "application/json", temperature: 0.3 },
    }),
  });
  const data = await res.json();
  const text = (data.candidates?.[0]?.content?.parts || []).map((p) => p.text || "").join("");
  if (!text) throw new Error("gemini failed: " + JSON.stringify(data).slice(0, 200));
  const json = text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1);
  return JSON.parse(json);
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

  try {
    // 2) auth GCP -> 3) embed en Vertex -> 4) cosine -> 5) Gemini en Vertex
    const token = await getAccessToken(env);
    const qvec = await embed(message, token);
    const hits = topK(qvec, 3);
    const context = hits.map((h) => `[${h.id}] ${h.text}`).join("\n\n");
    const out = await askGemini(context, message, token);

    const routing = out?.triage?.routing;
    const kind = routing === "kb_autoresolve" ? "rag" : "escalated";
    return json({ answer: out.answer, triage: out.triage, kind });
  } catch (e) {
    return json({ error: "server error", detail: String(e).slice(0, 200) }, 500);
  }
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
