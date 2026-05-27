"""ArUco marker detector.

Wave 1.5 shell:
  - Uses OpenCV's built-in ArUco (DICT_4X4_50) when cv2 is available.
  - Gracefully returns an empty detection if cv2 is not installed
    (the rest of the system can boot — V-Agent + PE flow degrade nicely).

Detection semantics (per Protocol § Vision design):
  - A marker that is *visible* = not currently being touched
  - A marker that *disappears for ≥ N seconds* = the學員 is touching that
    anatomical region (hand occludes the marker)
  - Caller (router) is responsible for tracking marker presence across
    frames and emitting "region touched" events.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from src.vision.anatomy_map import ANATOMY_MARKERS, AnatomyRegion, marker_to_region

logger = logging.getLogger(__name__)


@dataclass
class MarkerDetection:
    """Single ArUco marker detected in a frame."""

    aruco_id: int
    region: AnatomyRegion | None  # None if id is outside our anatomy map
    # corner pixel coords (4 × (x, y)) — frontend uses these for overlay
    corners: list[tuple[float, float]] = field(default_factory=list)
    center: tuple[float, float] = (0.0, 0.0)


@dataclass
class DetectionResult:
    """Per-frame detection summary."""

    detections: list[MarkerDetection] = field(default_factory=list)
    frame_h: int = 0
    frame_w: int = 0
    backend: str = "stub"  # 'opencv' when cv2 ok; 'stub' when missing


class MarkerDetector:
    """Wrapper around cv2.aruco — lazy-loaded.

    On systems without OpenCV the detector returns empty DetectionResult,
    so the API can be exercised end-to-end before the GPU box has cv2.
    """

    def __init__(self) -> None:
        self._cv2: Any | None = None
        self._aruco: Any | None = None
        self._dict: Any | None = None
        self._params: Any | None = None
        self._available: bool | None = None  # tri-state: None=unknown

    def _ensure_loaded(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import cv2  # type: ignore[import-untyped]
            self._cv2 = cv2
            self._aruco = cv2.aruco  # type: ignore[attr-defined]
            self._dict = self._aruco.getPredefinedDictionary(self._aruco.DICT_4X4_50)
            self._params = self._aruco.DetectorParameters()
            self._available = True
            logger.info("ArUco detector initialised (DICT_4X4_50)")
        except Exception as exc:
            logger.warning("OpenCV ArUco unavailable: %s", exc)
            self._available = False
        return self._available

    def detect(self, frame: Any) -> DetectionResult:
        """Run ArUco detection on a single frame (numpy BGR ndarray)."""
        if frame is None or not self._ensure_loaded():
            return DetectionResult(backend="stub")

        cv2 = self._cv2
        aruco = self._aruco
        assert cv2 is not None and aruco is not None  # for mypy

        h, w = frame.shape[:2]
        # cv2.aruco API changed in 4.7+ — use the new ArucoDetector if present.
        try:
            detector = aruco.ArucoDetector(self._dict, self._params)
            corners, ids, _ = detector.detectMarkers(frame)
        except AttributeError:
            corners, ids, _ = aruco.detectMarkers(frame, self._dict, parameters=self._params)

        detections: list[MarkerDetection] = []
        if ids is not None:
            for marker_corners, mid in zip(corners, ids.flatten()):
                pts = marker_corners.reshape(-1, 2)
                cx = float(pts[:, 0].mean())
                cy = float(pts[:, 1].mean())
                detections.append(
                    MarkerDetection(
                        aruco_id=int(mid),
                        region=marker_to_region(int(mid)),
                        corners=[(float(x), float(y)) for x, y in pts],
                        center=(cx, cy),
                    )
                )

        return DetectionResult(
            detections=detections, frame_h=int(h), frame_w=int(w), backend="opencv"
        )


@lru_cache
def get_marker_detector() -> MarkerDetector:
    return MarkerDetector()


def occluded_regions(
    last_seen: dict[int, float],
    now: float,
    occlusion_threshold_s: float = 1.5,
) -> list[AnatomyRegion]:
    """Helper for the per-session marker tracker: which regions have been
    occluded (i.e. *not* detected) for ≥ threshold seconds?

    Args:
        last_seen: { aruco_id: epoch_seconds_last_visible }
        now: current epoch seconds
        occlusion_threshold_s: how long a marker must stay missing before
            we call the region "touched".

    Returns:
        List of AnatomyRegion currently considered touched. Markers
        outside ANATOMY_MARKERS are ignored.
    """
    out: list[AnatomyRegion] = []
    for aid, spec in ANATOMY_MARKERS.items():
        ts = last_seen.get(aid)
        if ts is None:
            continue  # never seen — student hasn't started, or marker absent
        if now - ts >= occlusion_threshold_s:
            out.append(spec.region)
    return out
