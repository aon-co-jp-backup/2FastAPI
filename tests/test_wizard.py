import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from tofastapi import web
from tofastapi.i18n import LANGS, S, text

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", "examples", "django_proj"))


def test_all_languages_have_all_keys():
    keys = set(S["en"])
    assert len(LANGS) == 14  # default + 13
    for code, _, _ in LANGS:
        if code != "default":
            assert set(S[code]) == keys, code
    assert "English" not in text("default", "close") and "Close" in text("default", "close") and "閉じる" in text("default", "close")
    assert "{n}" not in text("ru", "found", n=3)


@pytest.fixture()
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), web._Handler)
    web._Handler.token = "tok"
    web._Handler.port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield "http://127.0.0.1:%d" % web._Handler.port
    srv.shutdown()


def call(base, method, body, token="tok", host=None):
    h = {"content-type": "application/json", "x-token": token}
    if host:
        h["Host"] = host
    req = urllib.request.Request(base + "/tofastapi.v1.Wizard/" + method, json.dumps(body).encode(), h)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_page_and_auth(server):
    page = urllib.request.urlopen(server + "/").read().decode()
    assert "2FastAPI" in page and "tok" in page
    assert call(server, "ListDir", {}, token="bad")[0] == 403
    assert call(server, "ListDir", {}, host="evil.example")[0] == 403
    assert call(server, "Nope", {})[0] == 404


def test_scan_and_convert(server, tmp_path):
    st, j = call(server, "Scan", {"path": os.path.dirname(PROJ)})
    assert st == 200 and any(p["kind"] == "django" for p in j["projects"])
    dj = [p for p in j["projects"] if p["kind"] == "django"][0]
    out = str(tmp_path / "out")
    st, r = call(server, "Convert", {"path": os.path.dirname(PROJ), "dest": out, "target": "mfastapi", "names": [dj["path"]]})
    assert st == 200 and r["n"] == 1, r
    assert os.path.isfile(os.path.join(out, "run_mfastapi.py"))
    assert "mfastapi" in open(os.path.join(out, "requirements.txt")).read()
    assert call(server, "Convert", {"path": PROJ, "dest": PROJ})[0] == 400
