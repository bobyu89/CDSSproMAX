"""MarkerDetector — graceful degradation + occlusion tracking semantics."""

from src.vision.anatomy_map import AnatomyRegion
from src.vision.marker_detector import (
    DetectionResult,
    MarkerDetector,
    occluded_regions,
)


def test_detect_on_none_frame_returns_empty():
    det = MarkerDetector()
    result = det.detect(None)
    assert isinstance(result, DetectionResult)
    assert result.detections == []


def test_occluded_regions_no_samples_returns_empty():
    assert occluded_regions(last_seen={}, now=100.0) == []


def test_occluded_regions_below_threshold():
    # Marker last seen 1.0s ago (threshold default 1.5s) — not yet touched.
    last_seen = {1: 99.0}  # marker id 1 → PMI
    regions = occluded_regions(last_seen, now=100.0)
    assert regions == []


def test_occluded_regions_above_threshold():
    # Marker last seen 2.0s ago — counts as touched.
    last_seen = {1: 98.0}
    regions = occluded_regions(last_seen, now=100.0)
    assert regions == [AnatomyRegion.PMI]


def test_occluded_regions_above_max_window_treated_as_absent():
    """Bug fix from review: marker seen once long ago must NOT be reported
    as touched forever. After max_touch_window_s (default 8s), the marker
    is considered just absent (out of frame / lighting issue)."""
    last_seen = {1: 50.0}  # 50s ago — way past 8s window
    regions = occluded_regions(last_seen, now=100.0)
    assert regions == []


def test_occluded_regions_at_max_window_still_touched():
    # gap == max_touch_window_s → still counts (inclusive upper bound)
    last_seen = {1: 92.0}  # 8.0s ago
    regions = occluded_regions(last_seen, now=100.0)
    assert regions == [AnatomyRegion.PMI]


def test_occluded_regions_custom_max_window():
    last_seen = {1: 95.0}  # 5s ago
    # With max=3, marker is considered absent
    assert (
        occluded_regions(last_seen, now=100.0, max_touch_window_s=3.0) == []
    )
    # With max=10, still touched
    assert (
        occluded_regions(last_seen, now=100.0, max_touch_window_s=10.0)
        == [AnatomyRegion.PMI]
    )


def test_occluded_regions_ignores_unmapped_ids():
    last_seen = {1: 98.0, 999: 0.0}  # 999 not in ANATOMY_MARKERS
    regions = occluded_regions(last_seen, now=100.0)
    assert regions == [AnatomyRegion.PMI]


def test_occluded_threshold_configurable():
    last_seen = {1: 99.5}  # 0.5s ago
    assert occluded_regions(last_seen, now=100.0, occlusion_threshold_s=0.3) == [
        AnatomyRegion.PMI
    ]
    assert occluded_regions(last_seen, now=100.0, occlusion_threshold_s=1.0) == []


def test_multiple_regions_touched_simultaneously():
    last_seen = {1: 95.0, 13: 95.0, 2: 99.8}  # PMI + RUQ touched; aortic still visible
    regions = sorted(r.value for r in occluded_regions(last_seen, now=100.0))
    assert regions == [AnatomyRegion.ABD_RUQ.value, AnatomyRegion.PMI.value]


def test_get_marker_detector_is_singleton():
    from src.vision.marker_detector import get_marker_detector

    a = get_marker_detector()
    b = get_marker_detector()
    assert a is b
