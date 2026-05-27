"""Frame decoding helpers.

Wave 1.5 shell: accepts a base64-encoded JPEG/PNG from the frontend and
returns a numpy array. OpenCV is imported lazily so the rest of the
backend can boot without it installed.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

# Numpy is used for type annotations only (lazy import in functions)


def _np():  # local lazy import
    import numpy as np
    return np


def decode_frame(data: bytes | str) -> Any:
    """Decode JPEG/PNG bytes (or base64 string) → numpy BGR ndarray.

    Returns None if the payload is empty or undecodable; caller decides
    how to surface that to the user.
    """
    if isinstance(data, str):
        # Strip optional data URL prefix
        if "," in data and data.startswith("data:"):
            data = data.split(",", 1)[1]
        try:
            data = base64.b64decode(data)
        except Exception:
            return None

    if not data:
        return None

    try:
        import cv2  # type: ignore[import-untyped]
        import numpy as np

        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img  # may be None if decode fails
    except ImportError:
        # OpenCV not installed yet — return raw bytes wrapped so callers
        # can detect the shape without crashing.
        return None


def encode_jpeg(frame: Any, quality: int = 80) -> bytes | None:
    """Encode an ndarray back to JPEG bytes (for debug overlay storage)."""
    try:
        import cv2

        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        return bytes(buf) if ok else None
    except ImportError:
        return None
    except Exception:
        return None


def frame_dims(frame: Any) -> tuple[int, int] | None:
    """Return (height, width) of the frame, or None if invalid."""
    if frame is None:
        return None
    try:
        h, w = frame.shape[:2]
        return int(h), int(w)
    except Exception:
        return None
