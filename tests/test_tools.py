from coreldraw_agent.backend import MockBackend
from coreldraw_agent.tools import dispatch


def test_dispatch_draws():
    b = MockBackend()
    assert dispatch(b, "new_document", {"width": 100, "height": 100}).startswith("ok")
    assert dispatch(b, "polygon", {"points": [[0, 0], [10, 0], [5, 8]], "fill": "#ff0000"}).startswith("ok")
    assert b.calls[1][1][0] == [(0, 0), (10, 0), (5, 8)]


def test_errors_are_returned_not_raised():
    b = MockBackend()
    assert dispatch(b, "nope", {}).startswith("error")
    assert dispatch(b, "rectangle", {"x": 1}).startswith("error")
