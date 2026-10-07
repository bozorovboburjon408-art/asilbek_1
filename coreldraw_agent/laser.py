"""Raster image -> CO2 laser cut geometry (CorelDRAW SVG layout).

Dark shape on light background (or transparent PNG) becomes closed cut
contours: each part is one compound path = outer outline + its holes.
Units are millimetres, origin bottom-left, Y up.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

Point = tuple[float, float]
Part = list[list[Point]]  # [outer, hole, hole, ...]

STROKE = "#373435"  # single colour used in the Corel SVG layout


@dataclass
class LaserResult:
    parts: list[Part]
    width_mm: float
    height_mm: float
    warnings: list[str] = field(default_factory=list)


def _load_gray(path: str) -> np.ndarray:
    data = np.fromfile(path, dtype=np.uint8)  # works with non-ASCII Windows paths
    img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    if img.ndim == 3 and img.shape[2] == 4:  # transparent -> white
        a = img[:, :, 3:4].astype(np.float32) / 255
        img = (img[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def trace(path: str, width_mm: float, *, material_mm: float = 3.0, invert: bool = False,
          threshold: int | None = None, simplify_mm: float = 0.1,
          min_area_mm2: float = 4.0, sheet: tuple[float, float] = (700, 600),
          margin_mm: float = 10.0) -> LaserResult:
    gray = _load_gray(path)
    h_px, w_px = gray.shape
    if threshold is None:
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    else:
        _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    if invert:
        mask = 255 - mask
    mask = cv2.copyMakeBorder(mask, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)

    scale = width_mm / w_px  # mm per pixel
    height_mm = h_px * scale
    sw, sh = sheet
    if width_mm + 2 * margin_mm > sw or height_mm + 2 * margin_mm > sh:
        raise ValueError(f"{width_mm:.0f}x{height_mm:.0f} mm does not fit the {sw:.0f}x{sh:.0f} mm sheet")

    contours, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    eps = max(simplify_mm / scale, 0.5)

    def to_mm(c) -> list[Point]:
        c = cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float)
        return [(margin_mm + (x - 2) * scale, margin_mm + (h_px - (y - 2)) * scale) for x, y in c]

    warnings: list[str] = []
    parts: list[Part] = []
    if hier is None:
        return LaserResult([], width_mm, height_mm, ["no shape found - try invert or a threshold"])
    hier = hier[0]
    small = 0
    for i, c in enumerate(contours):
        if hier[i][3] != -1:  # holes are attached to their parent below
            continue
        if cv2.contourArea(c) * scale * scale < min_area_mm2:
            small += 1
            continue
        outer = to_mm(c)
        if len(outer) < 3:
            continue
        part: Part = [outer]
        j = hier[i][2]
        while j != -1:
            hc = contours[j]
            area = cv2.contourArea(hc) * scale * scale
            if area >= min_area_mm2 / 4:
                hole = to_mm(hc)
                if len(hole) >= 3:
                    part.append(hole)
                    d = 2 * (area / np.pi) ** 0.5
                    if d < material_mm:
                        warnings.append(f"hole ~{d:.1f} mm is smaller than material {material_mm:g} mm")
            j = hier[j][0]
        parts.append(part)
    if small:
        warnings.append(f"{small} tiny speck(s) under {min_area_mm2:g} mm2 ignored")
    if not parts:
        warnings.append("no shape found - try invert or a threshold")
    return LaserResult(parts, width_mm, height_mm, warnings)


def to_svg(parts: list[Part], sheet: tuple[float, float] = (700, 600)) -> str:
    """CorelDRAW-style SVG: 1 unit = 0.01 mm, fil0/str0 classes, one path per part."""
    w, h = sheet
    paths = []
    for part in parts:
        d = ""
        for sub in part:
            pts = [(round(x * 100), round((h - y) * 100)) for x, y in sub]  # SVG Y is down
            d += "M%d %d " % pts[0] + " ".join("L%d %d" % p for p in pts[1:]) + " Z "
        paths.append(f'   <path class="fil0 str0" fill-rule="evenodd" d="{d.strip()}"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}mm" height="{h:g}mm" '
        f'viewBox="0 0 {w * 100:g} {h * 100:g}">\n'
        f' <defs><style type="text/css">.fil0 {{fill:none}} '
        f'.str0 {{stroke:{STROKE};stroke-width:20}} '
        f'.str1 {{stroke:{STROKE};stroke-width:1}}</style></defs>\n'
        ' <g id="Layer_x0020_1">\n' + "\n".join(paths) + "\n </g>\n</svg>\n"
    )


def cut_to_corel(backend, result: LaserResult, sheet: tuple[float, float] = (700, 600)) -> str:
    backend.new_document(*sheet)
    for part in result.parts:
        backend.compound(part, outline=STROKE, outline_width=0.2)
    return f"{len(result.parts)} part(s) drawn"


def run_image(path: str, width_mm: float, backend=None, svg_path: str | None = None, **kw) -> LaserResult:
    """Trace `path`, always write an SVG next to it, draw in CorelDRAW if a backend is given."""
    res = trace(path, width_mm, **kw)
    sheet = kw.get("sheet", (700, 600))
    out = Path(svg_path) if svg_path else Path(path).with_suffix(".laser.svg")
    out.write_text(to_svg(res.parts, sheet), encoding="utf-8")
    if backend is not None and res.parts:
        cut_to_corel(backend, res, sheet)
    return res
