import importlib.util
import os
import sys
import tempfile

from tofastapi import convert_flask


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def convert_and_load(src_path):
    with open(src_path, encoding="utf-8") as fh:
        res = convert_flask(fh.read())
    d = tempfile.mkdtemp()
    out = os.path.join(d, "converted_app.py")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(res.code)
    return res, load(out, "converted_" + os.path.basename(d))


def body_of(resp):
    ct = resp.headers.get("content-type", "")
    if "json" in ct:
        return resp.json()
    return resp.text
