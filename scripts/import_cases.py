"""Import cases from data/cases/*.md into the cases table.

Wave 1 scope: minimal viable import — store the raw markdown so cases can be
referenced by code/title. Full structured parsing (PE items, differential
diagnosis, rubric mapping) lands in a later step when the LLM-assisted case
parser is built.

Usage (from repo root, with the api venv active or via uv):

    uv run --project apps/api python scripts/import_cases.py
"""

from __future__ import annotations

import asyncio
import re
import sys
import uuid
from pathlib import Path

# Make `src.*` importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from sqlalchemy import select  # noqa: E402

from src.db.models import Case  # noqa: E402
from src.db.session import AsyncSessionLocal  # noqa: E402

CASES_DIR = REPO_ROOT / "data" / "cases"
FILENAME_RE = re.compile(r"^CASE-(\d+)_(.+)\.md$")


def parse_filename(path: Path) -> tuple[str, str] | None:
    m = FILENAME_RE.match(path.name)
    if not m:
        return None
    code = f"CASE-{m.group(1)}"
    slug = m.group(2)
    return code, slug


def extract_title(md_text: str, fallback: str) -> str:
    for line in md_text.splitlines():
        stripped = line.lstrip("# ").strip()
        if stripped:
            return stripped[:200]
    return fallback


def extract_chief_complaint(md_text: str) -> str:
    """Naive — first paragraph after '## 臨床情境'. Good enough for Wave 1."""
    in_section = False
    buf: list[str] = []
    for line in md_text.splitlines():
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() in ("## 臨床情境", "## 病史")
            continue
        if in_section and line.strip():
            buf.append(line.strip())
    return " ".join(buf)[:2000] or "(no chief complaint extracted)"


async def import_one(md_path: Path) -> str:
    parsed = parse_filename(md_path)
    if parsed is None:
        return f"SKIP {md_path.name} (filename pattern mismatch)"
    code, slug = parsed
    md = md_path.read_text(encoding="utf-8")

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(Case).where(Case.code == code))
        if existing:
            return f"SKIP {code} (already imported)"

        case = Case(
            id=uuid.uuid4(),
            code=code,
            title=extract_title(md, fallback=slug),
            chief_complaint=extract_chief_complaint(md),
            scenario_json={
                "source_file": md_path.name,
                "slug": slug,
                "raw_markdown": md,
            },
        )
        db.add(case)
        await db.commit()
        return f"OK   {code} ({case.title[:40]}...)"


async def main():
    if not CASES_DIR.exists():
        raise SystemExit(f"data/cases not found at {CASES_DIR}")
    md_files = sorted(CASES_DIR.glob("CASE-*.md"))
    if not md_files:
        raise SystemExit("No CASE-*.md files found.")

    print(f"Importing {len(md_files)} case(s) from {CASES_DIR}")
    for f in md_files:
        msg = await import_one(f)
        print(f"  {msg}")


if __name__ == "__main__":
    asyncio.run(main())
