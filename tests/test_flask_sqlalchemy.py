"""Flask-SQLAlchemy -> SQLAlchemy shim (differential)."""
import os

from fastapi.testclient import TestClient

from helpers import convert_and_load, load

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", "flask_app4", "app.py")


def test_models_and_queries():
    fl = load(APP, "orig_flask_app4").app.test_client()
    res, mod = convert_and_load(APP)
    fa = TestClient(mod.app)
    seq = [("GET", "/items", None), ("POST", "/items", {"name": "a"}), ("POST", "/items", {"name": "b"}),
           ("GET", "/items", None), ("GET", "/items/2", None), ("GET", "/items/9", None)]
    for m, u, j in seq:
        a = fl.open(u, method=m, json=j)
        b = fa.request(m, u, json=j)
        assert a.status_code == b.status_code, (m, u, a.status_code, b.status_code, b.text)
        if a.status_code != 404:
            assert a.get_json() == b.json(), (m, u)
