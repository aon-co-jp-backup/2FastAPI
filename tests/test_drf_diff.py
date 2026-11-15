import json
import os
import subprocess
import sys

import pytest

from tofastapi.django_conv import convert_project

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, "..", "examples", "drf_proj"))

REQUESTS = [
    ["GET", "/api/ping/", {}],
    ["GET", "/api/echo/?q=zed", {}],
    ["GET", "/api/echo/", {}],
    ["POST", "/api/echo/", {"json": {"name": "amy"}}],
    ["POST", "/api/echo/", {"json": {}}],
    ["GET", "/api/things/3/", {}],
    ["GET", "/api/things/9/", {}],
    ["POST", "/api/make/", {"json": {"text": "hello", "priority": 2}}],
    ["POST", "/api/make/", {"json": {"text": "x", "done": True, "ratio": 0.25}}],
    ["GET", "/api/notes/", {}],
    ["GET", "/api/notes/?limit=1", {}],
    ["POST", "/api/notes/", {"json": {"text": "hi"}}],
    ["POST", "/api/notes/", {"json": {}}],
    ["GET", "/api/notes/1/", {}],
    ["GET", "/api/notes/7/", {}],
    ["DELETE", "/api/notes/2/", {}],
]


def drf_results(req):
    p = subprocess.run([sys.executable, os.path.join(HERE, "run_drf_reference.py"), PROJ, req], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def converted(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("drfout"))
    res = convert_project(PROJ, out)
    req = os.path.join(out, "_req.json")
    json.dump(REQUESTS, open(req, "w"))
    p = subprocess.run([sys.executable, os.path.join(HERE, "run_requests.py"), out, req], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return res, json.loads(p.stdout.strip().splitlines()[-1]), out


def test_same_responses(converted):
    _, fa, out = converted
    dr = drf_results(os.path.join(out, "_req.json"))
    for (m, url, _), a, b in zip(REQUESTS, dr, fa):
        assert a[0] == b[0], (m, url, a, b)
        if a[0] < 400 and a[1] != "":
            assert a[1] == b[1], (m, url, a, b)


def test_serializer_became_model(converted):
    res, _, out = converted
    src = open(os.path.join(out, "api", "views.py")).read()
    assert "class NoteSerializer(BaseModel)" in src
    assert "rest_framework" not in src
    assert res.routes == 8
