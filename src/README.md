# `src/` — mapa de módulos

De 24 archivos, **solo ~7 son el producto vivo**; el resto es andamiaje (generar el dataset, publicarlo, exportar). Esta guía dice qué es qué.

## 🟢 Núcleo — el producto (RAG + triage en vivo)
| Archivo | Qué hace |
|---|---|
| `embed.py` | Embeddings vía Vertex `text-embedding-005` (768-dim). **Base compartida** (retrieval + features). |
| `chunk_kb.py` | Parte la KB en chunks para el retrieval. |
| `vectorstore.py` | Retrieval por **cosine exacto** (brute-force, sin vector DB) sobre Mongo. |
| `rag.py` | Respuesta grounded: recupera chunks y el LLM responde o rechaza honesto. |
| `triage.py` | Pipeline unificado — la puerta de entrada que une clasificación + RAG. |
| `mongo_store.py` | MongoDB = system-of-record de la app (el foro). |
| `responses.py` | Genera la respuesta de cada ticket y la persiste en Mongo (alimenta la UI). |

## 🔵 ML — el clasificador de triage
| Archivo | Qué hace |
|---|---|
| `features.py` | Arma la matriz de features (embeddings crudos) para el clasificador. |
| `classify.py` | Entrena una LR por etiqueta + **evalúa** (split 80/20, accuracy + macro-F1). |

## 🟡 Generar dataset (one-time, no corre en producción)
| Archivo | Qué hace |
|---|---|
| `taxonomy.py` | Catálogo de escenarios (bundles topic/type/priority/routing). |
| `events.py` | Catálogo de eventos (outages + launches) para la capa temporal. |
| `sampler.py` | Muestreo reproducible de tickets. |
| `prompts.py` | Prompts de generación (voz de cliente, sin fugas de etiqueta). |
| `generate_tickets.py` | Genera tickets base (CLI). |
| `generate_event_layer.py` | Genera la capa de eventos encima del baseline. |
| `generate_dataset.py` | Runner resumible que produce el dataset completo. |
| `assemble.py` | Une los archivos mensuales en el dataset final. |
| `build_kb.py` | Genera los artículos de la KB. |

## 🟠 Publicar (one-time)
| Archivo | Qué hace |
|---|---|
| `publish_hf.py` | Sube el dataset a Hugging Face. |
| `publish_kaggle.py` | Espejo del dataset en Kaggle. |

## 🟣 Exportar al worker (puentes a producción)
| Archivo | Qué hace |
|---|---|
| `export_kb_vectors.py` | Exporta los 89 chunks + vectores → JSON bundleado en el Worker. |
| `export_foro.py` | Exporta tickets respondidos de Mongo → JSON estático para el foro. |
| `classifier_weights.json` *(en `worker/`)* | Pesos de la LR exportados para inferencia en JS (ver `notebooks/01_export_classifier.ipynb`). |

## ⚪ Infra
| Archivo | Qué hace |
|---|---|
| `llm.py` | Cliente LLM (Anthropic/Vertex) para la generación sintética. |
| `__init__.py` | Marca `src/` como paquete. |

---
**Nota:** todo se importa con `from src.X import ...`. Si algún día se reorganiza en subcarpetas (`core/`, `datagen/`, etc.), hay que actualizar ~28 imports cruzados + el notebook + referencias del worker. Por eso hoy solo se documenta, no se mueve.
