"""Flask-Login -> session shim (differential)."""
import os

from fastapi.testclient import TestClient

from helpers import convert_and_load, load

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", "flask_app5", "app.py")


def test_login_flow():
    fl = load(APP, "orig_flask_app5").app.test_client()
    res, mod = convert_and_load(APP)
    fa = TestClient(mod.app, follow_redirects=False)
    seq = [("GET", "/me"), ("GET", "/private"), ("POST", "/signin/9"), ("POST", "/signin/2"), ("GET", "/me"),
           ("GET", "/private"), ("POST", "/signout"), ("GET", "/private"), ("GET", "/me")]
    for m, u in seq:
        a = fl.open(u, method=m)
        b = fa.request(m, u)
        assert a.status_code == b.status_code, (m, u, a.status_code, b.status_code, b.text)
        if a.status_code == 302:
            assert a.headers["Location"] == b.headers["location"], (a.headers["Location"], b.headers["location"])
        elif a.is_json and b.headers.get("content-type", "").startswith("application/json") and a.status_code != 401:
            assert a.get_json() == b.json(), (m, u)
