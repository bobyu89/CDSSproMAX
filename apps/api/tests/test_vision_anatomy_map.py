"""Anatomy map — invariants between marker IDs and AnatomyRegion enum."""

from src.vision.anatomy_map import (
    ANATOMY_MARKERS,
    ANATOMY_REGIONS,
    AnatomyRegion,
    marker_to_region,
    region_to_marker,
)


def test_all_markers_have_unique_regions():
    regions = [spec.region for spec in ANATOMY_MARKERS.values()]
    assert len(regions) == len(set(regions)), "marker → region map must be bijective"


def test_marker_ids_contiguous_from_1():
    ids = sorted(ANATOMY_MARKERS.keys())
    assert ids == list(range(1, len(ids) + 1))


def test_reverse_lookup_round_trips():
    for aid, spec in ANATOMY_MARKERS.items():
        assert region_to_marker(spec.region) == aid


def test_lookup_unknown_id_is_none():
    assert marker_to_region(999) is None
    assert region_to_marker(AnatomyRegion("pmi")) == 1


def test_anatomy_regions_size_matches_markers():
    assert len(ANATOMY_REGIONS) == len(ANATOMY_MARKERS)


def test_minimum_marker_count_for_osce():
    # 15 markers cover心臟、頸部、肺、腹部 — must not silently shrink.
    assert len(ANATOMY_MARKERS) >= 15
