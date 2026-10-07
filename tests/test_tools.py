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


def test_close_subpath_fallbacks():
    from coreldraw_agent.backend import close_subpath

    class NoMethods:  # mimics a COM object that rejects CloseSubPath/Close
        def __init__(self): self.pts = []
        def AppendLineSegment(self, x, y): self.pts.append((x, y))
        def __getattr__(self, n): raise AttributeError(n)
        def __setattr__(self, n, v):
            if n == "Closed": raise AttributeError(n)
            object.__setattr__(self, n, v)

    class HasClosed(NoMethods):
        def __setattr__(self, n, v): object.__setattr__(self, n, v)

    a = NoMethods()
    close_subpath(a, (1, 2))
    assert a.pts == [(1, 2)]
    b = HasClosed()
    close_subpath(b, (1, 2))
    assert b.Closed is True and b.pts == []
