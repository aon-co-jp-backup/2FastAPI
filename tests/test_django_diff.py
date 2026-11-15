import json
import os
import subprocess
import sys
import tempfile

import pytest

from tofastapi.django_conv import convert_project

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", "examples", "django_proj"))

REQUESTS = [
    ["GET", "/", {}],
    ["GET", "/v2/", {}],
    ["GET", "/articles/2024/hello-world/", {}],
    ["GET", "/v2/articles/7/x/", {}],
    ["GET", "/search/?q=zed&page=3", {}],
    ["GET", "/search/", {}],
    ["POST", "/create/", {"data": {"name": "amy"}}],
    ["POST", "/create/", {"data": {}}],
    ["GET", "/items/2/", {}],
    ["GET", "/items/9/", {}],
    ["GET", "/both/", {}],
    ["POST", "/both/", {}],
    ["GET", "/go/", {}],
    ["GET", "/agent/", {"headers": {"X-Agent": "pytest"}}],
    ["GET", "/agent/", {}],
    ["GET", "/archive/2023/", {}],
]


def django_results():
    sys.path.insert(0, PROJ)
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(ROOT_URLCONF="config.urls", ALLOWED_HOSTS=["*"], DEBUG=False, SECRET_KEY="x", INSTALLED_APPS=[], DEFAULT_CHARSET="utf-8")
    django.setup()
    from django.test import Client

    c = Client()
    out = []
    for method, url, kw in REQUESTS:
        kw = dict(kw)
        headers = kw.pop("headers", {})
        extra = {"HTTP_" + k.upper().replace("-", "_"): v for k, v in headers.items()}
        data = kw.pop("data", None)
        if method == "GET":
            r = c.get(url, **extra)
        else:
            r = c.post(url, data=data or {}, **extra)
        ct = r.headers.get("Content-Type", "")
        body = json.loads(r.content) if "json" in ct else r.content.decode()
        out.append([r.status_code, body, r.headers.get("Location")])
    return out


@pytest.fixture(scope="module")
def converted(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("djout"))
    res = convert_project(PROJ, out)
    req = os.path.join(out, "_req.json")
    json.dump(REQUESTS, open(req, "w"))
    p = subprocess.run([sys.executable, os.path.join(HERE, "run_requests.py"), out, req], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return res, json.loads(p.stdout.strip().splitlines()[-1]), out


def test_same_responses(converted):
    _, fa, _ = converted
    dj = django_results()
    for (m, url, _), a, b in zip(REQUESTS, dj, fa):
        assert a[0] == b[0], (m, url, a, b)
        if a[0] < 400 and a[0] not in (301, 302):
            assert a[1] == b[1], (m, url, a, b)
        if a[0] in (301, 302):
            assert (a[2] or "").endswith("/") and (b[2] or "").endswith("/")


def test_routes_and_output(converted):
    res, _, out = converted
    assert res.routes == 18  # 9 views x 2 prefixes
    assert os.path.isfile(os.path.join(out, "main.py"))
    assert "uvicorn main:app" in open(os.path.join(out, "CONVERSION_REPORT.md")).read()
