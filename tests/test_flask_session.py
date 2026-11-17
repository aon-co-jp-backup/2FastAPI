"""flask.session -> request.session, flask.g -> request.state (differential)."""
import os

from fastapi.testclient import TestClient

from helpers import convert_and_load, load

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", "flask_app3", "app.py")


def test_session_and_g():
    fl = load(APP, "orig_flask_app3").app.test_client()
    res, mod = convert_and_load(APP)
    fa = TestClient(mod.app)
    for c, call in ((fl, lambda c, m, u: c.open(u, method=m)), (fa, lambda c, m, u: c.request(m, u))):
        seq = [call(c, "GET", "/whoami"), call(c, "POST", "/login/zed"), call(c, "GET", "/whoami"), call(c, "GET", "/count"), call(c, "GET", "/count")]
        out = [r.get_json() if hasattr(r, "get_json") else r.json() for r in seq]
        assert out == [{"user": "anonymous"}, {"ok": True}, {"user": "zed"}, {"n": 1, "tag": "t"}, {"n": 2, "tag": "t"}], out
    assert any("session" in str(w) for w in res.warnings)


def test_teardown_request():
    fl = load(APP, "orig_flask_app3b").app.test_client()
    res, mod = convert_and_load(APP)
    fa = TestClient(mod.app)
    for c, get in ((fl, lambda r: r.get_json()), (fa, lambda r: r.json())):
        c.get("/whoami")
        c.get("/whoami")
        # teardown runs after each request, so the third request sees the two earlier ones (+ itself not yet)
        assert get(c.get("/closed")) == {"closed": 2}
