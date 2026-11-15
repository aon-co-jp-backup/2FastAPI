# -*- coding: utf-8 -*-
"""Target "MFastAPI": the converted FastAPI app plus a launcher that calls mfastapi.accelerate(app)."""
from __future__ import annotations

import os


def _write(path: str, data: str, mode: str) -> None:
    with open(path, mode, encoding="utf-8", newline="\n") as fh:
        fh.write(data)


def apply_mfastapi(p, out_dir: str) -> None:
    entry = "main" if p.kind == "django" else (os.path.splitext(p.entry)[0].replace(os.sep, ".").replace("/", ".") or "main")
    _write(
        os.path.join(out_dir, "run_mfastapi.py"),
        "# MFastAPI: the converted FastAPI app with Rust route acceleration.\n"
        "# Run: uvicorn run_mfastapi:app --reload\n"
        "import mfastapi\n"
        "from %s import app\n\n"
        "mfastapi.accelerate(app)  # call after all routes are registered\n" % entry,
        "w",
    )
    _write(os.path.join(out_dir, "requirements.txt"), "fastapi\nuvicorn\nmfastapi\n", "w")
    rp = os.path.join(out_dir, "CONVERSION_REPORT.md")
    if os.path.isfile(rp):
        _write(
            rp,
            "\n## MFastAPI\n\nRun `pip install -r requirements.txt` then `uvicorn run_mfastapi:app --reload` "
            "(plain FastAPI behaviour if the Rust extension is unavailable).\n",
            "a",
        )
