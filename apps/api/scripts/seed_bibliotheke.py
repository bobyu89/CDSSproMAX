"""Seed the ``bibliotheke_chunks`` table from ``data/bibliotheke_seeds/*.md``.

Behaviour:
  - No .md files found  → log "no seed files found" and exit 0.
  - For each .md file: split on blank lines, then enforce ≤ 400 chars per chunk,
    embed via :class:`Embedder`, and insert as ``BibliothekeChunk`` rows.

Run from ``apps/api``::

    uv run python scripts/seed_bibliotheke.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Make ``src`` importable when run as a plain script
_API_ROOT = Path(__file__).resolve().parents[1]
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

from src.db.models import BibliothekeChunk  # noqa: E402
from src.db.session import AsyncSessionLocal  # noqa: E402
from src.rag.embedder import get_embedder  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_bibliotheke")

REPO_ROOT = Path(__file__).resolve().parents[3]
SEEDS_DIR = REPO_ROOT / "data" / "bibliotheke_seeds"
MAX_CHARS = 400


def _split_paragraph(p: str, max_chars: int = MAX_CHARS) -> list[str]:
    p = p.strip()
    if not p:
        return []
    if len(p) <= max_chars:
        return [p]
    return [p[i : i + max_chars] for i in range(0, len(p), max_chars)]


def _chunks_from_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    chunks: list[str] = []
    for para in text.split("\n\n"):
        chunks.extend(_split_paragraph(para))
    return chunks


async def _seed() -> int:
    if not SEEDS_DIR.exists():
        logger.info("seeds dir %s does not exist — nothing to do", SEEDS_DIR)
        return 0

    md_files = sorted(p for p in SEEDS_DIR.glob("*.md") if p.name.lower() != "readme.md")
    if not md_files:
        logger.info("no seed files found in %s", SEEDS_DIR)
        return 0

    embedder = get_embedder()
    inserted = 0

    async with AsyncSessionLocal() as session:
        for md in md_files:
            source = md.stem
            chunks = _chunks_from_file(md)
            if not chunks:
                logger.info("%s: no chunks", source)
                continue
            logger.info("%s: embedding %d chunks", source, len(chunks))
            vectors = await embedder.embed_texts(chunks)
            for content, vec in zip(chunks, vectors, strict=True):
                session.add(
                    BibliothekeChunk(
                        source=source,
                        content=content,
                        embedding=vec,
                        metadata_json={"file": md.name},
                    )
                )
                inserted += 1
        await session.commit()

    logger.info("inserted %d chunks across %d file(s)", inserted, len(md_files))
    return 0


def main() -> int:
    return asyncio.run(_seed())


if __name__ == "__main__":
    raise SystemExit(main())
