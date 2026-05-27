"""Rubric loader + LQQOPERA default-rubric integrity tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.rubric import (
    Rubric,
    RubricItem,
    load_lqqopera_default,
    load_rubric_from_file,
)

EXPECTED_LQQOPERA_IDS = {
    "lqqopera.location",
    "lqqopera.quality",
    "lqqopera.quantity",
    "lqqopera.onset",
    "lqqopera.precipitating",
    "lqqopera.extension",
    "lqqopera.relieving",
    "lqqopera.associated_symptoms",
}


def test_load_lqqopera_default_returns_rubric():
    rubric = load_lqqopera_default()
    assert isinstance(rubric, Rubric)
    assert rubric.rubric_id == "lqqopera.v1"
    assert rubric.type == "lqqopera"


def test_lqqopera_has_all_eight_dimensions():
    rubric = load_lqqopera_default()
    assert len(rubric.items) == 8
    ids = {item.id for item in rubric.items}
    assert ids == EXPECTED_LQQOPERA_IDS


def test_lqqopera_each_item_covers_levels_0_and_5():
    rubric = load_lqqopera_default()
    for item in rubric.items:
        assert len(item.criteria) >= 4, f"{item.id} has < 4 criteria"
        levels = {c.level for c in item.criteria}
        assert 0 in levels, f"{item.id} missing level 0 descriptor"
        assert 5 in levels, f"{item.id} missing level 5 descriptor"


def test_lqqopera_evidence_anchors_present():
    rubric = load_lqqopera_default()
    for item in rubric.items:
        assert item.evidence_anchors, f"{item.id} missing evidence_anchors"


def test_get_item_lookup():
    rubric = load_lqqopera_default()
    item = rubric.get_item("lqqopera.location")
    assert item is not None
    assert item.dimension == "Location"
    assert rubric.get_item("lqqopera.does_not_exist") is None


def test_pydantic_validation_rejects_bad_level(tmp_path: Path):
    bad = {
        "rubric_id": "bad.v1",
        "type": "lqqopera",
        "items": [
            {
                "id": "bad.item",
                "dimension": "Bad",
                "criteria": [{"level": 99, "descriptor": "out of range"}],
            }
        ],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_rubric_from_file(path)


def test_pydantic_validation_rejects_empty_descriptor(tmp_path: Path):
    bad = {
        "rubric_id": "bad.v1",
        "type": "lqqopera",
        "items": [
            {
                "id": "bad.item",
                "dimension": "Bad",
                "criteria": [{"level": 3, "descriptor": "   "}],
            }
        ],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_rubric_from_file(path)


def test_rubric_item_pe_optional_fields():
    """PE-only fields should be valid but optional."""
    item = RubricItem(
        id="pe.lung.auscultation.right_lower",
        dimension="Auscultation",
        body_region="right_lower_lung",
        expected_action="auscultation",
        min_duration_seconds=3.0,
        criteria=[{"level": 5, "descriptor": "完整聽診"}],
    )
    assert item.expected_action == "auscultation"
    assert item.min_duration_seconds == 3.0
