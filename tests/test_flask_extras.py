"""fresh_login_required / request_loader / unauthorized_handler / paginate (differential)."""
import os

from fastapi.testclient import TestClient

from helpers import convert_and_load, load

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", "flask_app6", "app.py")


def test_extras():
    fl = load(APP, "orig_flask_app6").app.test_client()
    res, mod = convert_and_load(APP)
    fa = TestClient(mod.app, follow_redirects=False)
    seq = [("GET", "/items?page=1", {}), ("GET", "/items?page=3", {}), ("GET", "/fresh", {}),
           ("GET", "/fresh", {"X-Token": "tok"}), ("POST", "/signin", {}), ("GET", "/fresh", {})]
    for m, u, h in seq:
        a = fl.open(u, method=m, headers=h)
        b = fa.request(m, u, headers=h)
        assert a.status_code == b.status_code, (m, u, a.status_code, b.status_code, b.text)
        if a.is_json:
            assert a.get_json() == b.json(), (m, u, a.get_json(), b.json())
