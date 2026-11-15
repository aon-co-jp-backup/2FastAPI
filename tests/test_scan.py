"""Scan + interactive driver: several systems below one directory."""
import json
import os
import shutil
import subprocess
import sys

import pytest

from tofastapi.scan import run_auto, scan

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.abspath(os.path.join(HERE, "..", "examples"))


@pytest.fixture()
def workspace(tmp_path):
    ws = tmp_path / "ws"
    shutil.copytree(os.path.join(EX, "django_proj"), ws / "shop" / "backend")
    shutil.copytree(os.path.join(EX, "flask_app"), ws / "api")
    shutil.copytree(os.path.join(EX, "flask_app2"), ws / "tools" / "books")
    (ws / "venv" / "lib" / "site-packages").mkdir(parents=True)
    (ws / "venv" / "lib" / "site-packages" / "x.py").write_text("from flask import Flask\napp = Flask(__name__)\n")
    (ws / "docs").mkdir()
    (ws / "docs" / "readme.py").write_text("print('hi')\n")
    return ws


def test_scan_finds_three_systems_and_skips_venv(workspace):
    ps = scan(str(workspace))
    kinds = sorted((p.kind, p.name) for p in ps)
    assert kinds == [("django", "backend"), ("flask", "api"), ("flask", "books")]
    assert all("venv" not in p.path for p in ps)
    assert next(p for p in ps if p.name == "books").routes >= 3


def test_auto_yes_creates_folders(workspace, tmp_path):
    out = tmp_path / "newdir" / "result"  # does not exist
    msgs = []
    res = run_auto(str(workspace), str(out), assume_yes=True, say=msgs.append)
    assert len(res) == 3
    assert (out / "backend" / "main.py").is_file()
    assert (out / "api" / "CONVERSION_REPORT.md").is_file()
    assert any("作成" in m for m in msgs)  # Japanese text is printed next to the English


def test_auto_asks_bilingual_questions_and_honours_no(workspace, tmp_path):
    out = tmp_path / "out"
    asked = []
    answers = iter(["2,3", "", "n", "y"])  # select, (dest accepted by -o => no dest question), create? n / y

    def ask(q):
        asked.append(q)
        return next(answers)

    res = run_auto(str(workspace), str(out), ask=ask, say=lambda m: None)
    assert any("Convert which?" in q and "どれを" in q for q in asked)
    assert any("Create it?" in q and "作成しますか" in q for q in asked)
    assert len(res) == 1  # first answer "n" skipped one folder, second "y" created the other
    assert out.is_dir()


def test_cli_scan_json(workspace):
    p = subprocess.run([sys.executable, "-m", "tofastapi", "scan", str(workspace), "--json"], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    data = json.loads(p.stdout)
    assert {d["kind"] for d in data} == {"flask", "django"}


def test_cli_convert(workspace, tmp_path):
    out = tmp_path / "o"
    api = workspace / "api"
    p = subprocess.run([sys.executable, "-m", "tofastapi", "convert", "--kind", "flask", "--path", str(api), "-o", str(out), "--json"], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)["routes"] > 0
    assert (out / "CONVERSION_REPORT.md").is_file()
