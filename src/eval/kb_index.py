"""Chunking de la KB para el eval — la MISMA construcción que midió el discovery.

El corpus etiquetado (spec eval.md §2) usa chunk_id = `source::heading` (minúsculas,
espacios→guiones), el esquema del discovery (`scripts/discovery/observe_flow.py`).
Este módulo replica esa construcción 1:1 para que las etiquetas del corpus y el
índice del eval hablen el mismo idioma de ids.

OJO: NO es el chunker de `src/chunk_kb.py` (ids `stem#i`, incluye intros — 90 chunks).
La divergencia entre ambos esquemas está registrada en bitacora/hallazgos.md y la
resuelve la regla de paridad JS/Python de eval.md §4 cuando POL-7 toque el índice.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

# raíz del repo (este archivo vive en src/eval/)
REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / "kb"


def load_kb_chunks(kb_dir: Path | None = None) -> list[dict]:
    """Chunkea la KB por secciones H2 — réplica exacta del chunker del discovery.

    Reglas heredadas (no "mejorarlas": cambiarlas invalida las etiquetas del corpus):
    - solo secciones `## ` (el intro antes del primer H2 no genera chunk);
    - se descarta cualquier sección cuyo cuerpo contenga "still stuck?" (el footer
      boilerplate — efecto colateral conocido: también cae la última sección del
      artículo cuando el footer quedó dentro de su cuerpo);
    - texto del chunk = "{titulo}\\n\\n## {heading}\\n\\n{cuerpo}".
    """
    chunks: list[dict] = []
    for md_path in sorted((kb_dir or KB_DIR).glob("*.md")):
        source = md_path.stem
        title = ""
        current_heading: str | None = None
        current_body: list[str] = []

        def flush() -> None:
            # guarda el bloque acumulado como chunk si tiene contenido útil
            if current_heading is None:
                return
            body = "\n".join(current_body).strip()
            if not body or "still stuck?" in body.lower():
                return
            chunks.append(
                {
                    "chunk_id": f"{source}::{current_heading.lower().replace(' ', '-')}",
                    "source": source,
                    "title": title,
                    "heading": current_heading,
                    "text": f"{title}\n\n## {current_heading}\n\n{body}",
                }
            )

        for line in md_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# ") and not title:
                title = stripped[2:].strip()
            elif stripped.startswith("## "):
                flush()
                current_heading = stripped[3:].strip()
                current_body = []
            elif current_heading is not None:
                current_body.append(line)
        flush()

    return chunks


def kb_index_hash(chunks: list[dict]) -> str:
    """Hash corto del contenido del índice (ids + textos, en orden).

    Identifica la versión exacta de la KB en el reporte (eval.md §4: "un número
    sin su config no es evidencia"). Si un artículo cambia, el hash cambia.
    """
    h = hashlib.sha256()
    for c in chunks:
        h.update(c["chunk_id"].encode("utf-8"))
        h.update(b"\x00")
        h.update(c["text"].encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:12]


if __name__ == "__main__":
    kb = load_kb_chunks()
    print(f"{len(kb)} chunks · hash {kb_index_hash(kb)}")
    for c in kb:
        print(" ", c["chunk_id"])
