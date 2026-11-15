"""Differential test: the same requests against the Flask original and the converted FastAPI app."""
import os

import pytest
from fastapi.testclient import TestClient

from helpers import body_of, convert_and_load, load

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "examples", "flask_app", "app.py")

REQUESTS = [
    ("GET", "/", {}),
    ("GET", "/items/1", {}),
    ("GET", "/items/2", {}),
    ("GET", "/items/99", {}),
    ("GET", "/search?q=hi&limit=5", {}),
    ("GET", "/search", {}),
    ("POST", "/echo", {"json": {"a": 1, "b": [1, 2]}}),
    ("POST", "/form", {"data": {"name": "bob"}}),
    ("POST", "/form", {"data": {}}),
    ("GET", "/hdr", {"headers": {"X-Agent": "pytest"}}),
    ("GET", "/hdr", {}),
    ("GET", "/files/a/b/c.txt", {}),
    ("GET", "/both", {}),
    ("POST", "/both", {}),
    ("GET", "/api/ping", {}),
    ("GET", "/api/sum/2/40", {}),
    ("GET", "/nope", {}),
]


@pytest.fixture(scope="module")
def apps():
    flask_mod = load(APP, "orig_flask_app")
    res, fa_mod = convert_and_load(APP)
    return flask_mod.app.test_client(), TestClient(fa_mod.app, follow_redirects=False), res


@pytest.mark.parametrize("method,url,kw", REQUESTS)
def test_same_response(apps, method, url, kw):
    fl, fa, _ = apps
    a = fl.open(url, method=method, **kw)
    b = fa.request(method, url, **kw)
    assert a.status_code == b.status_code, (a.status_code, b.status_code, a.get_data(as_text=True), b.text)
    if a.status_code < 400:
        ba = a.get_json() if a.is_json else a.get_data(as_text=True)
        assert ba == body_of(b)


def test_redirect(apps):
    fl, fa, _ = apps
    a = fl.get("/old")
    b = fa.get("/old")
    assert a.status_code == b.status_code == 302
    assert a.headers["Location"].endswith("/") and b.headers["location"].endswith("/")


def test_route_count(apps):
    assert apps[2].routes == 11
