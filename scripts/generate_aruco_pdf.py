"""Generate a printable A4 PDF of all 15 anatomy ArUco markers.

Each page has one large marker (~5×5 cm) + label + print hint. Print
on plain A4 paper, cut out, and attach to the half-body mannequin per
the print_hint instructions.

Usage:
    uv run --project apps/api python scripts/generate_aruco_pdf.py \
        --out data/aruco/anatomy_markers.pdf
"""

from __future__ import annotations

import argparse
import sys
from io import BytesIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from src.vision.anatomy_map import ANATOMY_MARKERS  # noqa: E402

MARKER_PX = 600  # rendered marker size in pixels (will be scaled by reportlab)
MARKER_CM = 5.0  # printed size


def render_marker_png(aruco_id: int) -> bytes:
    """Render a single ArUco marker as a PNG byte string."""
    try:
        import cv2  # type: ignore[import-untyped]
        import numpy as np  # noqa: F401
    except ImportError:
        raise SystemExit(
            "OpenCV is required to generate marker PNGs. "
            "Run: uv pip install opencv-python  (under apps/api)"
        )

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    img = cv2.aruco.generateImageMarker(aruco_dict, aruco_id, MARKER_PX)
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError(f"failed to encode marker {aruco_id} to PNG")
    return bytes(buf)


def build_pdf(out_path: Path) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    except ImportError:
        raise SystemExit(
            "reportlab is required. Run: uv pip install reportlab  (under apps/api)"
        )

    # Use a CJK-capable font so 繁體中文 labels render.
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        FONT = "STSong-Light"
    except Exception:
        FONT = "Helvetica"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(out_path), pagesize=A4)
    page_w, page_h = A4

    for aruco_id, spec in ANATOMY_MARKERS.items():
        png_bytes = render_marker_png(aruco_id)

        # Header
        c.setFont(FONT, 20)
        c.drawString(2 * cm, page_h - 2.5 * cm, f"ArUco #{aruco_id}")
        c.setFont(FONT, 14)
        c.drawString(2 * cm, page_h - 3.5 * cm, spec.label_zh)
        c.setFont(FONT, 10)
        c.drawString(2 * cm, page_h - 4.3 * cm, f"region: {spec.region.value}")

        # Marker — centered, MARKER_CM × MARKER_CM
        marker_w = MARKER_CM * cm
        x = (page_w - marker_w) / 2
        y = (page_h - marker_w) / 2 - 1 * cm
        from reportlab.lib.utils import ImageReader

        c.drawImage(
            ImageReader(BytesIO(png_bytes)),
            x,
            y,
            width=marker_w,
            height=marker_w,
            mask="auto",
        )

        # Print hint
        c.setFont(FONT, 12)
        c.drawCentredString(page_w / 2, y - 1 * cm, f"貼附位置：{spec.print_hint}")

        # Footer / instructions
        c.setFont(FONT, 8)
        c.drawCentredString(
            page_w / 2,
            1.5 * cm,
            "請以實際比例 (1:1) 列印，不要縮放。 DICT_4X4_50",
        )
        c.showPage()

    c.save()
    print(f"✓ Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "data" / "aruco" / "anatomy_markers.pdf",
    )
    args = parser.parse_args()
    build_pdf(args.out)


if __name__ == "__main__":
    main()
