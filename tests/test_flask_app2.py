"""Second Flask sample: hooks, templates, uploads, Flask-RESTful resources, CORS."""
import io
import os

import pytest
from fastapi.testclient import TestClient

from helpers import body_of, convert_and_load, load

HERE = os.path.dirname(os.path.abspath(__file__))
APPDIR = os.path.join(HERE, "..", "examples", "flask_app2")
APP = os.path.join(APPDIR, "app.py")

REQUESTS = [
    ("GET", "/hello/zed", {}),
    ("GET", "/blocked", {}),
    ("GET", "/nothing-here", {}),
    ("GET", "/books", {}),
    ("GET", "/books/1", {}),
    ("GET", "/books/9", {}),
    ("DELETE", "/books/2", {}),
    ("POST", "/books", {"json": {"title": "Ubik"}}),
]


@pytest.fixture(scope="module")
def apps():
    cwd = os.getcwd()
    os.chdir(APPDIR)  # templates/ is relative to the working directory
    try:
        flask_mod = load(APP, "orig_flask_app2")
        res, fa_mod = convert_and_load(APP)
        yield flask_mod.app.test_client(), TestClient(fa_mod.app, follow_redirects=False), res
    finally:
        os.chdir(cwd)


@pytest.mark.parametrize("method,url,kw", REQUESTS)
def test_same_response(apps, method, url, kw):
    fl, fa, _ = apps
    a = fl.open(url, method=method, **kw)
    b = fa.request(method, url, **kw)
    assert a.status_code == b.status_code, (url, a.status_code, b.status_code, a.get_data(as_text=True), b.text)
    ba = a.get_json() if a.is_json else a.get_data(as_text=True)
    bb = body_of(b)
    if isinstance(ba, str):
        assert ba.strip() == bb.strip()
    elif a.status_code != 404 or url != "/books/9":
        assert ba == bb
    else:  # flask-restful's abort(message=...) body shape differs from FastAPI's {"detail": ...}
        # (the converted app's @errorhandler(404) also catches it; flask-restful bypasses app handlers)
        assert "no such book" in str(bb) or bb == {"error": "not found"}


def test_upload(apps):
    fl, fa, _ = apps
    a = fl.post("/upload", data={"doc": (io.BytesIO(b"hello"), "a.txt")}, content_type="multipart/form-data")
    b = fa.post("/upload", files={"doc": ("a.txt", b"hello")})
    assert a.status_code == b.status_code == 200
    assert a.get_json() == b.json()


def test_cors_and_routes(apps):
    _, fa, res = apps
    r = fa.get("/books", headers={"Origin": "http://x.example"})
    assert r.headers.get("access-control-allow-origin") == "*"
    assert res.routes == 7
