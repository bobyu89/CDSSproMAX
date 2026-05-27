"""Vision layer — ArUco marker detection + V-Agent (Gemini Vision).

Wave 1.5 scope:
  - Marker detection: OpenCV ArUco (CPU-only, deterministic, sub-second)
  - V-Agent: Gemini 3.5 Flash multimodal call on keyframes
  - Anatomy mapping: 15 ArUco IDs → solid半身假人 解剖位置 對應表
  - Frame capture: base64/multipart → numpy ndarray helper

Per Protocol design choice:
  Layer 1 (markers) solves position with deterministic confidence (~80%)
  Layer 2 (V-Agent) judges手法 / 姿態 / 持續時間 with LLM (~20%)
"""

from src.vision.anatomy_map import (
    ANATOMY_MARKERS,
    ANATOMY_REGIONS,
    AnatomyRegion,
    marker_to_region,
)
from src.vision.frame_capture import decode_frame, encode_jpeg
from src.vision.marker_detector import (
    DetectionResult,
    MarkerDetection,
    MarkerDetector,
    get_marker_detector,
)

__all__ = [
    "ANATOMY_MARKERS",
    "ANATOMY_REGIONS",
    "AnatomyRegion",
    "DetectionResult",
    "MarkerDetection",
    "MarkerDetector",
    "decode_frame",
    "encode_jpeg",
    "get_marker_detector",
    "marker_to_region",
]
