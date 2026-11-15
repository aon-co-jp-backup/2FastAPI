"""Command line: `2fastapi flask app.py -o app_fastapi.py` / `2fastapi django project_dir -o out_dir`."""
from __future__ import annotations

import argparse
import os
import sys

from . import __version__


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="2fastapi", description="Convert Flask / Django code to FastAPI (MFastAPI compatible).")
    ap.add_argument("--version", action="version", version="2fastapi " + __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("flask", help="convert a Flask module")
    f.add_argument("path")
    f.add_argument("-o", "--output", help="output file (default: stdout)")
    d = sub.add_parser("django", help="convert a Django project/app (urls.py + views.py)")
    d.add_argument("path", help="project directory (containing manage.py) or an app directory")
    d.add_argument("-o", "--output", required=True, help="output directory")
    a = sub.add_parser("auto", help="detect Flask or Django and convert")
    a.add_argument("path")
    a.add_argument("-o", "--output", required=True)
    ns = ap.parse_args(argv)

    cmd = ns.cmd
    if cmd == "auto":
        cmd = "django" if os.path.isdir(ns.path) else "flask"
    if cmd == "flask":
        from .flask_conv import convert_source

        with open(ns.path, encoding="utf-8") as fh:
            src = fh.read()
        res = convert_source(src)
        out_path = getattr(ns, "output", None)
        if out_path:
            if os.path.isdir(out_path) or out_path.endswith(("/", "\\")):
                os.makedirs(out_path, exist_ok=True)
                out_path = os.path.join(out_path, os.path.basename(ns.path))
            with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(res.code)
            print("wrote %s (%d routes)" % (out_path, res.routes), file=sys.stderr)
        else:
            sys.stdout.write(res.code)
        for w in res.warnings:
            print("warning: %s" % w, file=sys.stderr)
        return 0
    from .django_conv import convert_project

    res = convert_project(ns.path, ns.output)
    print("wrote %s (%d routes)" % (ns.output, res.routes), file=sys.stderr)
    for w in res.warnings:
        print("warning: %s" % w, file=sys.stderr)
    return 0
