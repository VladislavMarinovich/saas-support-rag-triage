# Bitácora — Polaris demo (estado vivo)

> Log de estado + plan para reorientarse rápido (incl. después de un compact).
> Se actualiza a medida que avanzamos. Fecha última: 2026-07-30 (mid-refactor Mongo).

## Norte
Portfolio flagship de empleabilidad (AI Engineer). Sistema: **support triage + RAG**
sobre un dataset sintético de un SaaS ficticio ("Polaris"). El *fin* es el empleo; el
demo es el vehículo.

## ✅ Hecho
- **Dataset v2** (23.994 tickets, capa de eventos, 2024→jun-2026) generado por
  trimestres y verificado. Publicado en **HF** (`VladislavMarinovich/polaris-support-tickets-v2`)
  y **Kaggle** (`vladislavmarinovich1/polaris-support-tickets-v2`), CC BY-SA 4.0, con
  card, descripción, portada, thumbnail 564×284 y notebook EDA.
- **Clasificador** reentrenado sobre v2 (topic .997/type .996/priority .995/routing
  acc .996 F1 .978/sentiment .871) + **curva de aprendizaje** (`classifier_eval.ipynb`).
- **Auditoría de labels**: `security_incident` inflado (841→77; 764 eran outages de
  dashboards → re-ruteados a `engineering`). Documentado como pieza de portafolio.
- **README** del repo con hero (firma temporal). 5 notebooks. **Ledger de costos**
  (`docs/costs.md`, ~$3.35/$100). **ADR 0001** (quitar vector DB → cosine sobre Mongo).

## ✅ Consolidado a MongoDB (un solo store) — ADR 0001 CERRADO
- [x] **Atlas M0 conectado.** Cluster `polariscluster` (AWS us-east-1), DB = `polaris`,
  `MONGODB_URI` en `.env`. `python -m src.mongo_store --ping` → OK.
- [x] **24k tickets cargados** → `polaris.tickets` (23.994). Índices: ticket_id (unique),
  created_at.
- [x] **89 chunks KB + vectores → `polaris.kb_chunks`** (doc: chunk_id, source, title,
  heading, text, vector). Vía `index_kb()` en el nuevo `vectorstore.py`.
- [x] **`src/vectorstore.py` reescrito** → SIN Pinecone. `index_kb()` (chunk→embed→upsert
  a Mongo) + `search(query, top_k=3)` = **cosine exacto** (numpy, cache en memoria),
  DEVUELVE `[(chunk_id, score, text)]` (shape intacto → `rag.py` NO se tocó salvo docstring).
- [x] **RAG verificado**: HubSpot→responde (top 0.825, idéntico al benchmark), "book
  flights"→rechaza (0.545), TikTok→espera honesta (roadmap 0.473). ✔
- [x] **Pinecone quitado**: `uv remove pinecone`; `.env.example` ahora tiene `MONGODB_URI`
  (fuera `PINECONE_API_KEY`); README (stack + fila RAG) actualizado con nota ADR.

## ⏭️ Pendiente
- [ ] **Respuestas** (alimentan la UI): acks **templados** para 9.905 escalados (sin
  LLM, ~$0) + respuestas **RAG** para 14.089 kb_autoresolve (~$2.54; muestra ~300
  primero, luego decidir bulk). Guardar en Mongo (ticket + triage + respuesta).
- [ ] **UI**: foro (lee Mongo, respuestas pre-computadas) + chat en vivo. Stack:
  Cloudflare Pages+Workers + Mongo, o Gradio/HF Spaces. **NO BuddyPress.** Ojo:
  Worker no corre Python → el chat RAG va por API directa o mini-servicio.
- [ ] Publicar el notebook EDA en Kaggle (web: Import → **Add Input** el dataset →
  Run All → Save). *El "sin gráficos" era por no montar el dataset como Input.*
- [ ] **LinkedIn** la otra semana (viernes = mal día): ángulo del **label-audit**, o
  bundle con el demo vivo. Redactar cuando toque.

## 🧭 Decisiones clave
- **Estrategia de respuesta:** kb_autoresolve→respuesta RAG (LLM); escalado→ack
  templado (sin LLM). Usa el LLM solo donde agrega valor (decisión FinOps).
- **Retrieval:** cosine exacto sobre 89 vectores en Mongo (ADR 0001); brute-force es
  óptimo a este tamaño (benchmark 0.824 in-memory vs 0.825 Pinecone). Vector DB solo
  cuando el corpus lo amerite (>~10-100k).
- **Embeddings:** Vertex `text-embedding-005` (768d). **LLM:** Gemini
  `gemini-2.5-flash-lite` (bulk) / Anthropic Haiku.
- **Budget:** $100 GCP (excluye Mongo). Mongo M0 = gratis para siempre (sin cliff nov).
- **Handles:** GitHub/HF = `VladislavMarinovich`; Kaggle = `vladislavmarinovich1`.
- **Regla honestidad:** dato sintético → scores altos por construcción; decirlo. En
  entrevista: método/pipeline, no "modelo infalible".

## 🔐 Secrets (`.env`, NUNCA en chat/git)
`ANTHROPIC_API_KEY` · `GOOGLE_CLOUD_PROJECT=polaris-triage-demo` (ADC, re-auth con
`gcloud auth application-default login` cuando expire) · `HF_TOKEN` · `KAGGLE_API_TOKEN`
· `MONGODB_URI`. (Pinecone eliminado — ver ADR 0001.)

## 🗂️ Mapa de archivos (clave)
- `src/`: taxonomy, sampler, prompts, events, generate_event_layer, generate_dataset,
  embed, vectorstore, chunk_kb, rag, features, classify, triage, llm, mongo_store,
  publish_hf, publish_kaggle.
- `notebooks/`: eda_v2 (+ _es), classifier_eval, kaggle_eda.
- `docs/`: hf-dataset-card, kaggle-description, costs, BITACORA, adr/0001.
- `data/` (gitignored): tickets_v2.jsonl, .parquet, .csv, ticket_features_v2.npy.
