"""Chunk the Polaris knowledge base for retrieval.

Strategy: STRUCTURAL, section-level. Each markdown `##` section becomes one
chunk, with the document title (and heading) prepended so the chunk is
self-contained — e.g. "Dashboard won't load > Verify connector status: ...".

Why section-level (see docs/dataset-spec.md discussion): our KB articles are
small (~370 tokens) and already cleanly sectioned, so the section *is* the unit
of one self-contained answer. No fixed-size splitting or overlap needed.

The boilerplate "Still stuck? contact support" footer is stripped — it's
identical across every article and would pollute every chunk with noise.

Run:  python -m src.chunk_kb
"""

from __future__ import annotations

import glob
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    chunk_id: str   # e.g. "dashboards-not-loading#2"
    source: str     # source article filename (stem)
    title: str      # document title
    heading: str | None  # section heading (None for the intro block)
    text: str       # the embeddable text (title + heading + body)


def chunk_article(path: str) -> list[Chunk]:
    """Split one KB markdown file into section-level chunks."""
    stem = Path(path).stem
    raw = Path(path).read_text(encoding="utf-8")
    # Drop the shared boilerplate footer ("---\n**Still stuck?** ...").
    raw = re.split(r"\n-{3,}\s*\n+\*\*Still stuck", raw)[0].strip()

    lines = raw.splitlines()
    title = lines[0].lstrip("#").strip()  # first line is the "# Article title"

    # Segment into (heading | None, body_lines): the first segment (before any
    # ##) is the intro and carries heading=None. Walk the lines; each "## " opens
    # a new section, everything else accumulates into the current section's body.
    segments: list[tuple[str | None, list[str]]] = []
    heading: str | None = None
    body: list[str] = []
    for line in lines[1:]:
        if line.startswith("## "):
            if body:
                segments.append((heading, body))
            heading, body = line.lstrip("#").strip(), []
        else:
            body.append(line)
    if body:
        segments.append((heading, body))

    # Turn each section into a self-contained chunk: prepend the doc title (and
    # heading) so the chunk carries its own context even if it's one sentence.
    chunks: list[Chunk] = []
    for i, (heading, body) in enumerate(segments):
        text_body = "\n".join(body).strip()
        if not text_body:
            continue
        prefix = f"{title} > {heading}" if heading else title
        chunks.append(Chunk(
            chunk_id=f"{stem}#{i}",
            source=stem,
            title=title,
            heading=heading,
            text=f"{prefix}\n{text_body}",
        ))
    return chunks


def chunk_kb(pattern: str = "kb/*.md") -> list[Chunk]:
    """Chunk every KB article."""
    chunks: list[Chunk] = []
    for path in sorted(glob.glob(pattern)):
        chunks.extend(chunk_article(path))
    return chunks


if __name__ == "__main__":
    all_chunks = chunk_kb()
    lengths = [len(c.text) for c in all_chunks]
    print(f"{len(all_chunks)} chunks from KB")
    print(f"chunk length (chars): min {min(lengths)} | mean {sum(lengths)//len(lengths)} "
          f"| max {max(lengths)}   (~{sum(lengths)//len(lengths)//4} tokens avg)\n")

    print("=== chunks of kb/dashboards-not-loading.md ===")
    for c in chunk_article("kb/dashboards-not-loading.md"):
        print("-" * 70)
        print(f"[{c.chunk_id}]  heading={c.heading!r}")
        print(c.text)
