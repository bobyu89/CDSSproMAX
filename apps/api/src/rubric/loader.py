"""Rubric file loaders.

The LQQOPERA default rubric is the Wave-1 centrepiece content asset; it
lives at ``data/rubrics/lqqopera.json`` (repo root). Other rubrics (PE,
custom case-specific ones) load via ``load_rubric_from_file``.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.config import REPO_ROOT
from src.rubric.schema import Rubric

DEFAULT_LQQOPERA_PATH = REPO_ROOT / "data" / "rubrics" / "lqqopera.json"


def load_rubric_from_file(path: Path) -> Rubric:
    """Load and validate a rubric JSON file from disk.

    Raises:
        FileNotFoundError: if the path does not exist.
        pydantic.ValidationError: if the file fails schema validation.
    """
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return Rubric.model_validate(data)


def load_lqqopera_default() -> Rubric:
    """Load the canonical LQQOPERA 8-dimension rubric shipped in this repo."""
    return load_rubric_from_file(DEFAULT_LQQOPERA_PATH)
