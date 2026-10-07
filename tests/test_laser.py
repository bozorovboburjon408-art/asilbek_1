import cv2
import numpy as np

from coreldraw_agent.backend import MockBackend
from coreldraw_agent.laser import run_image, to_svg, trace
from coreldraw_agent.tools import dispatch


def _ring(path):
    img = np.full((400, 400), 255, np.uint8)
    cv2.circle(img, (200, 200), 150, 0, -1)
    cv2.circle(img, (200, 200), 60, 255, -1)
    cv2.imwrite(str(path), img)


def test_ring_is_one_part_with_one_hole(tmp_path):
    _ring(tmp_path / "ring.png")
    res = trace(str(tmp_path / "ring.png"), 100)
    assert len(res.parts) == 1 and len(res.parts[0]) == 2
    xs = [x for x, _ in res.parts[0][0]]
    assert abs((max(xs) - min(xs)) - 75) < 2  # 300px of 400px at 100 mm


def test_svg_and_corel(tmp_path):
    _ring(tmp_path / "ring.png")
    b = MockBackend()
    res = run_image(str(tmp_path / "ring.png"), 100, b)
    svg = (tmp_path / "ring.laser.svg").read_text(encoding="utf-8")
    assert 'viewBox="0 0 70000 60000"' in svg and "fil0 str0" in svg and svg.count(" Z") == 2
    assert [c[0] for c in b.calls] == ["new_document", "compound"] and res.warnings == []


def test_too_big_rejected(tmp_path):
    _ring(tmp_path / "ring.png")
    try:
        trace(str(tmp_path / "ring.png"), 690)
    except ValueError as e:
        assert "does not fit" in str(e)
    else:
        raise AssertionError


def test_compound_tool():
    b = MockBackend()
    assert dispatch(b, "compound", {"paths": [[[0, 0], [9, 0], [9, 9]], [[1, 1], [2, 1], [2, 2]]]}).startswith("ok")
