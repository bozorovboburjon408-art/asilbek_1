"""Tool schemas exposed to the model and their dispatcher."""
from __future__ import annotations

from typing import Any

from .backend import Backend

_STYLE = {
    "fill": {"type": "string", "description": "Fill colour, #RRGGBB"},
    "outline": {"type": "string", "description": "Outline colour, #RRGGBB"},
    "outline_width": {"type": "number", "description": "Outline width in mm"},
}


def _tool(name: str, desc: str, props: dict, required: list[str], style=True):
    props = {**props, **(_STYLE if style else {})}
    return {
        "name": name,
        "description": desc + " Units: mm, origin bottom-left, Y up.",
        "input_schema": {"type": "object", "properties": props, "required": required},
    }


_N = {"type": "number"}
TOOLS: list[dict[str, Any]] = [
    _tool("new_document", "Create a new page of the given size.",
          {"width": _N, "height": _N}, ["width", "height"], style=False),
    _tool("rectangle", "Draw a rectangle from its bottom-left corner.",
          {"x": _N, "y": _N, "w": _N, "h": _N}, ["x", "y", "w", "h"]),
    _tool("ellipse", "Draw an ellipse (circle if rx == ry) around a centre.",
          {"cx": _N, "cy": _N, "rx": _N, "ry": _N}, ["cx", "cy", "rx", "ry"]),
    _tool("line", "Draw a straight line.",
          {"x1": _N, "y1": _N, "x2": _N, "y2": _N}, ["x1", "y1", "x2", "y2"]),
    _tool("polygon", "Draw a closed polygon through the given points.",
          {"points": {"type": "array", "minItems": 3,
                      "items": {"type": "array", "items": _N, "minItems": 2, "maxItems": 2}}},
          ["points"]),
    _tool("text", "Add artistic text with baseline-left at (x, y).",
          {"x": _N, "y": _N, "text": {"type": "string"}, "size": {"type": "number", "description": "Font size in pt"}},
          ["x", "y", "text", "size"]),
    _tool("save", "Save the document as .cdr.", {"path": {"type": "string"}}, ["path"], style=False),
    _tool("export", "Export to .png or .pdf.", {"path": {"type": "string"}}, ["path"], style=False),
]


def dispatch(backend: Backend, name: str, args: dict[str, Any]) -> str:
    """Run one tool call; always returns a string (errors included) for the model."""
    try:
        if name == "polygon":
            args = {**args, "points": [tuple(p) for p in args["points"]]}
        fn = getattr(backend, name, None)
        if name not in {t["name"] for t in TOOLS} or fn is None:
            return f"error: unknown tool {name!r}"
        return f"ok: {fn(**args)}"
    except Exception as exc:  # surfaced to the model so it can self-correct
        return f"error: {type(exc).__name__}: {exc}"
