"""Drawing backends.

`CorelBackend` drives a real CorelDRAW instance through COM (Windows only).
`MockBackend` records the calls so the agent can be developed and tested
anywhere. All coordinates are millimetres, origin at the page's bottom-left,
Y axis pointing up (CorelDRAW convention).
"""
from __future__ import annotations

from typing import Protocol

CDR_MILLIMETER = 3
CDR_PNG = 802


class Backend(Protocol):
    def new_document(self, width: float, height: float) -> str: ...
    def rectangle(self, x: float, y: float, w: float, h: float, **style) -> str: ...
    def ellipse(self, cx: float, cy: float, rx: float, ry: float, **style) -> str: ...
    def line(self, x1: float, y1: float, x2: float, y2: float, **style) -> str: ...
    def polygon(self, points: list[tuple[float, float]], **style) -> str: ...
    def text(self, x: float, y: float, text: str, size: float, **style) -> str: ...
    def save(self, path: str) -> str: ...
    def export(self, path: str) -> str: ...


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"colour must be #RRGGBB, got {hex_color!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class CorelBackend:
    def __init__(self, prog_id: str = "CorelDRAW.Application") -> None:
        import win32com.client  # type: ignore

        self.app = win32com.client.Dispatch(prog_id)
        self.app.Visible = True
        self.doc = None
        self._n = 0

    @property
    def layer(self):
        if self.doc is None:
            raise RuntimeError("no document: call new_document first")
        return self.doc.ActiveLayer

    def _style(self, shape, fill=None, outline=None, outline_width=None) -> str:
        if fill:
            shape.Fill.ApplyUniformFill(self.app.CreateRGBColor(*_rgb(fill)))
        if outline:
            shape.Outline.Color.RGBAssign(*_rgb(outline))
        if outline_width is not None:
            shape.Outline.Width = outline_width
        self._n += 1
        return f"shape_{self._n}"

    def new_document(self, width, height):
        self.doc = self.app.CreateDocument()
        self.doc.Unit = CDR_MILLIMETER
        self.doc.ActivePage.SetSize(width, height)
        return f"document {width}x{height} mm"

    def rectangle(self, x, y, w, h, **style):
        return self._style(self.layer.CreateRectangle2(x, y, w, h), **style)

    def ellipse(self, cx, cy, rx, ry, **style):
        return self._style(self.layer.CreateEllipse2(cx, cy, rx, ry), **style)

    def line(self, x1, y1, x2, y2, **style):
        style.setdefault("outline", "#000000")
        return self._style(self.layer.CreateLineSegment(x1, y1, x2, y2), **style)

    def polygon(self, points, **style):
        curve = self.app.CreateCurve(self.doc)
        sub = curve.CreateSubPath(*points[0])
        for p in points[1:]:
            sub.AppendLineSegment(*p)
        sub.CloseSubPath()
        return self._style(self.layer.CreateCurve(curve), **style)

    def text(self, x, y, text, size, fill=None, **style):
        shape = self.layer.CreateArtisticText(x, y, text)
        shape.Text.FontProperties.Size = size
        return self._style(shape, fill=fill)

    def save(self, path):
        self.doc.SaveAs(path)
        return path

    def export(self, path):
        if path.lower().endswith(".pdf"):
            self.doc.PublishToPDF(path)
        else:
            self.doc.Export(path, CDR_PNG, 0)  # cdrCurrentPage
        return path


class MockBackend:
    """Records every call; used by tests and `--dry-run`."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def _rec(self, name, *args, **kw) -> str:
        self.calls.append((name, args, kw))
        return f"{name}_{len(self.calls)}"

    def new_document(self, width, height):
        return self._rec("new_document", width, height)

    def rectangle(self, x, y, w, h, **s):
        return self._rec("rectangle", x, y, w, h, **s)

    def ellipse(self, cx, cy, rx, ry, **s):
        return self._rec("ellipse", cx, cy, rx, ry, **s)

    def line(self, x1, y1, x2, y2, **s):
        return self._rec("line", x1, y1, x2, y2, **s)

    def polygon(self, points, **s):
        return self._rec("polygon", points, **s)

    def text(self, x, y, text, size, **s):
        return self._rec("text", x, y, text, size, **s)

    def save(self, path):
        return self._rec("save", path)

    def export(self, path):
        return self._rec("export", path)
