"""Chunking de la KB para el eval — índice SANEADO (POL-11, subtarea 11.4).

El corpus etiquetado (spec eval.md §2) usa chunk_id = `source::heading` (minúsculas,
espacios→guiones), el esquema heredado del discovery (`scripts/discovery/observe_flow.py`).
Los ids no cambian: lo que cambió en 11.4 es CÓMO se trata el footer boilerplate.

Criterio vigente (el de producción, `src/chunk_kb.py`): **el footer de soporte se
strippea del texto crudo ANTES de segmentar por H2**.

Criterio anterior (defectuoso, kb-audit.md §3): descartaba cualquier sección cuyo
*cuerpo* contuviera "still stuck?". Como el footer vive al final del artículo, eso
borraba entera la última sección real de 18 de los 20 artículos originales —los dos
bloques de Troubleshooting de conectores entre ellos— y a la vez indexaba como chunk
los 2 footers que estaban bajo su propio `## Still stuck?`. Era un defecto del
instrumento de medición, no de la KB: producción nunca perdió esas secciones. El
daño medido sobre el baseline v1 está en kb-audit.md §3 (23 % de las queries
recibían un chunk que solo decía "contact support").

El stripping de acá cubre todas las variantes de footer presentes en `kb/` —línea
suelta, `**Still stuck?**`, precedida de `---`, y heading propio `## Still stuck?`—,
que es más de lo que cubre el split de `src/chunk_kb.py` (solo la variante con `---`).
Producción arrastra por eso 2 chunks de puro footer y algunos con el footer embebido;
corregirlo toca el pipeline congelado por kb-expansion.md §2, así que queda registrado
en hallazgos (11.4) y fuera de esta subtarea.

Diferencia restante con producción: este índice no genera chunk para el intro anterior
al primer H2. Es lo que separa la paridad JS/Python, diferida a POL-7 (eval.md §4).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# raíz del repo (este archivo vive en src/eval/)
REPO_ROOT = Path(__file__).resolve().parents[2]
KB_DIR = REPO_ROOT / "kb"


# Marca el inicio del footer de soporte en cualquiera de sus variantes: línea suelta
# ("Still stuck? ..."), en negrita ("**Still stuck?** ..."), o como heading propio
# ("## Still stuck?"). Se ancla al comienzo de línea para no cortar en una mención
# incidental a mitad de párrafo.
_FOOTER = re.compile(r"^\s*(?:#{1,6}\s*)?\*{0,2}still stuck", re.IGNORECASE)
_SEPARADOR = re.compile(r"^-{3,}\s*$")


def _strip_footer(raw: str) -> str:
    """Corta el footer de soporte del texto crudo, antes de segmentar por H2.

    Si el footer viene precedido por un separador `---`, corta desde el separador,
    para no dejar una regla horizontal colgando al final del último chunk.
    """
    lineas = raw.splitlines()
    for i, linea in enumerate(lineas):
        if not _FOOTER.match(linea):
            continue
        corte = i
        # retroceder sobre líneas vacías para incluir un `---` previo en el corte
        j = i - 1
        while j >= 0 and not lineas[j].strip():
            j -= 1
        if j >= 0 and _SEPARADOR.match(lineas[j].strip()):
            corte = j
        return "\n".join(lineas[:corte])
    return raw


def load_kb_chunks(kb_dir: Path | None = None) -> list[dict]:
    """Chunkea la KB por secciones H2, con el footer ya strippeado del crudo.

    Reglas (cambiarlas invalida las etiquetas del corpus — ver eval.md §2):
    - el footer de soporte se elimina ANTES de segmentar (criterio de producción);
    - una sección `## ` por chunk; el intro anterior al primer H2 no genera chunk;
    - se descarta la sección que quede vacía tras el stripping (era solo footer);
    - texto del chunk = "{titulo}\\n\\n## {heading}\\n\\n{cuerpo}".
    """
    chunks: list[dict] = []
    for md_path in sorted((kb_dir or KB_DIR).glob("*.md")):
        source = md_path.stem
        title = ""
        current_heading: str | None = None
        current_body: list[str] = []

        def flush() -> None:
            # guarda el bloque acumulado como chunk si quedó contenido tras el stripping
            if current_heading is None:
                return
            body = "\n".join(current_body).strip()
            if not body:
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

        for line in _strip_footer(md_path.read_text(encoding="utf-8")).splitlines():
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
