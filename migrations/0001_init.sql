-- Tickets en vivo capturados por el Worker (vista cliente en /cliente).
-- Un ticket = una conversación completa (turno 1 + follow-ups), identificada por ticket_id.
-- Capa OLTP en el borde (Cloudflare D1) — Mongo queda como store de la KB/analítica.
CREATE TABLE IF NOT EXISTS tickets (
  ticket_id TEXT PRIMARY KEY,   -- crypto.randomUUID() generado en el server (no identifica al usuario, solo la conversación)
  created   INTEGER NOT NULL,   -- epoch ms del primer turno
  updated   INTEGER NOT NULL,   -- epoch ms del último turno
  subject   TEXT,               -- asunto del turno 1 (puede ser vacío)
  thread    TEXT NOT NULL,      -- JSON: [{role, text}, ...] el hilo completo
  triage    TEXT,               -- JSON: el triage del turno 1 {topic,type,priority,routing,sentiment}
  status    TEXT NOT NULL       -- 'open' | 'resolved' | 'escalated'
);

-- El foro lista los más recientes primero.
CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets (created DESC);
