"""Scan a directory tree for Flask / Django projects (several systems at once) and convert them.

The scanner never imports or executes the scanned code; it only reads files.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "venv", ".venv", "env", ".env", "__pycache__", "site-packages",
    "build", "dist", ".tox", ".mypy_cache", ".pytest_cache", ".idea", ".vscode", "target", ".eggs",
}

_FLASK_APP = re.compile(r"\bFlask\s*\(")
_FLASK_IMPORT = re.compile(r"^\s*(from\s+flask(\.\w+)?\s+import|import\s+flask)\b", re.M)
_ROUTE = re.compile(r"@\s*\w+\.(route|get|post|put|delete|patch)\s*\(")
_URLPATTERNS = re.compile(r"^\s*urlpatterns\s*=", re.M)
_ROOT_URLCONF = re.compile(r"ROOT_URLCONF\s*=\s*['\"]([\w.]+)['\"]")


@dataclass
class Project:
    kind: str  # "flask" | "django"
    name: str
    path: str  # django: project directory; flask: directory holding the app
    entry: str = ""  # flask: the module that creates Flask(...)
    files: List[str] = field(default_factory=list)  # flask: modules that import flask (relative to path)
    routes: int = 0
    notes: List[str] = field(default_factory=list)
    detected: Dict = field(default_factory=dict)  # source versions found by versions.detect_source

    def to_dict(self) -> Dict:
        return asdict(self)


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _walk(root: str):
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS and not d.endswith(".egg-info"))
        yield dp, sorted(fns)


def scan(root: str) -> List[Project]:
    """Find Django projects, Django apps and Flask apps below `root` (which may itself be one)."""
    root = os.path.abspath(root)
    projects: List[Project] = []
    django_roots: List[str] = []
    for dp, fns in _walk(root):
        if "manage.py" in fns and not any(dp == r or dp.startswith(r + os.sep) for r in django_roots):
            if any(f == "settings.py" for _, ff in _walk(dp) for f in ff) or _has_settings_dir(dp):
                django_roots.append(dp)
    for dr in django_roots:
        p = Project("django", os.path.basename(dr) or dr, dr)
        p.routes = _count_routes_django(dr)
        p.notes.append("manage.py found")
        projects.append(p)
    # stand-alone Django apps (urls.py with urlpatterns but no manage.py above)
    for dp, fns in _walk(root):
        if any(dp == r or dp.startswith(r + os.sep) for r in django_roots):
            continue
        if "urls.py" in fns and _URLPATTERNS.search(_read(os.path.join(dp, "urls.py"))):
            p = Project("django", os.path.basename(dp) or dp, dp)
            p.routes = _count_routes_django(dp)
            p.notes.append("urls.py without manage.py: treated as a Django app")
            projects.append(p)
    claimed = [p.path for p in projects if p.kind == "django"]
    # Flask: every file that calls Flask(...) is an app entry; group by its directory
    flask_by_dir: Dict[str, Project] = {}
    for dp, fns in _walk(root):
        if any(dp == r or dp.startswith(r + os.sep) for r in claimed):
            continue
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            src = _read(os.path.join(dp, fn))
            if _FLASK_IMPORT.search(src) and _FLASK_APP.search(src):
                proj = flask_by_dir.get(dp)
                if proj is None:
                    proj = Project("flask", os.path.basename(dp) or dp, dp, entry=fn)
                    flask_by_dir[dp] = proj
                else:
                    proj.notes.append("several Flask() apps in this directory: %s" % fn)
    for dp, proj in flask_by_dir.items():
        # related modules: anything below this directory that imports flask (blueprints, helpers),
        # unless it belongs to another detected app directory nested deeper
        others = [d for d in flask_by_dir if d != dp and d.startswith(dp + os.sep)]
        for sp, fns in _walk(dp):
            if any(sp == o or sp.startswith(o + os.sep) for o in others):
                continue
            for fn in fns:
                if fn.endswith(".py"):
                    src = _read(os.path.join(sp, fn))
                    if _FLASK_IMPORT.search(src):
                        rel = os.path.relpath(os.path.join(sp, fn), dp)
                        proj.files.append(rel)
                        proj.routes += len(_ROUTE.findall(src))
        projects.append(proj)
    projects.sort(key=lambda p: (p.kind, p.path))
    uniq: Dict[str, int] = {}
    for p in projects:  # make names unique (the name is used as an output sub-directory)
        n = uniq.get(p.name, 0)
        uniq[p.name] = n + 1
        if n:
            p.name = "%s_%d" % (p.name, n + 1)
    return projects


def _has_settings_dir(d: str) -> bool:
    return os.path.isdir(os.path.join(d, "settings")) or any(
        os.path.isfile(os.path.join(d, sub, "settings.py")) for sub in os.listdir(d) if os.path.isdir(os.path.join(d, sub))
    )


def _count_routes_django(d: str) -> int:
    n = 0
    for dp, fns in _walk(d):
        if "urls.py" in fns:
            n += len(re.findall(r"\b(path|re_path|url)\s*\(", _read(os.path.join(dp, "urls.py"))))
    return n


# ---------------------------------------------------------------- conversion

def convert_project_to(p: Project, out_dir: str, target: str = "fastapi", fastapi_version: Optional[str] = None):
    """Convert one scanned project into `out_dir` (created if needed). Returns (routes, warnings).

    The source Flask/Django versions are detected automatically (p.detected, shown in CONVERSION_REPORT.md).
    `fastapi_version` selects the FastAPI version to generate for (default: latest).
    target="mfastapi" additionally writes run_mfastapi.py (mfastapi.accelerate(app)) and requirements.txt.
    """
    from . import versions as V

    ver = V.normalize_target(fastapi_version)
    routes, warns = _convert_project_to(p, out_dir)
    p.detected = V.detect_source(p.path, _project_sources(p))
    code_all = []
    for dp, _, fns in os.walk(out_dir):
        for fn in fns:
            if fn.endswith(".py"):
                fp = os.path.join(dp, fn)
                with open(fp, encoding="utf-8") as fh:
                    src = fh.read()
                new, notes = V.adapt_code(src, ver)
                if new != src:
                    with open(fp, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(new)
                warns += ["%s: %s" % (os.path.relpath(fp, out_dir), n) for n in notes]
                code_all.append(new)
    reqs = V.requirements(p.kind, ver, "\n".join(code_all))
    with open(os.path.join(out_dir, "requirements.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(reqs) + "\n")
    rp = os.path.join(out_dir, "CONVERSION_REPORT.md")
    with open(rp, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n## Versions\n\n- Source (detected): %s\n- Target FastAPI: %s\n" % ("; ".join(V.describe_source(p.detected)) or "unknown", ver))
    if target == "mfastapi":
        apply_mfastapi(p, out_dir)
    return routes, warns


def _project_sources(p: Project) -> List[str]:
    out = []
    if p.kind == "flask":
        for rel in p.files:
            out.append(_read(os.path.join(p.path, rel)))
    else:
        for dp, fns in _walk(p.path):
            for fn in fns:
                if fn in ("urls.py", "views.py", "settings.py"):
                    out.append(_read(os.path.join(dp, fn)))
    return out


from .mfastapi_target import apply_mfastapi  # noqa: E402


def _convert_project_to(p: Project, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    if p.kind == "django":
        from .django_conv import convert_project

        res = convert_project(p.path, out_dir)
        return res.routes, [str(w) for w in res.warnings]
    from .flask_conv import convert_source

    routes, warns = 0, []
    for rel in p.files:
        with open(os.path.join(p.path, rel), encoding="utf-8") as fh:
            res = convert_source(fh.read())
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest) or out_dir, exist_ok=True)
        with open(dest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(res.code)
        routes += res.routes
        warns += ["%s: %s" % (rel, w) for w in res.warnings]
    entry = os.path.splitext(p.entry)[0].replace(os.sep, ".")
    with open(os.path.join(out_dir, "CONVERSION_REPORT.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# 2FastAPI conversion report\n\nRoutes written: %d\nRun: `uvicorn %s:app --reload`\n\n## Warnings (manual work needed)\n\n" % (routes, entry))
        fh.write("\n".join("- %s" % w for w in warns) or "- none")
        fh.write("\n")
    return routes, warns


# ---------------------------------------------------------------- interactive driver (EN / JA)

def _t(en: str, ja: str) -> str:
    return "%s\n  %s" % (en, ja)


def default_out_root(src_root: str) -> str:
    src_root = os.path.abspath(src_root)
    return src_root.rstrip("\\/") + "-fastapi"


def _inside(child: str, parent: str) -> bool:
    child, parent = os.path.abspath(child), os.path.abspath(parent)
    return child == parent or child.startswith(parent + os.sep)


def run_auto(
    root: str,
    out_root: Optional[str] = None,
    assume_yes: bool = False,
    select: Optional[str] = None,
    fastapi_version: Optional[str] = None,
    ask: Optional[Callable[[str], str]] = None,
    say: Callable[[str], None] = print,
) -> List[Dict]:
    """Scan `root`, ask (English + Japanese) which projects to convert and where to put them, then convert.

    Returns one result dict per converted project. `ask`/`say` are injectable for tests and for the editor extension.
    """
    ask = ask or (lambda q: input(q))
    projects = scan(root)
    if not projects:
        say(_t("No Flask or Django project found under %s." % root, "%s の下に Flask / Django のプロジェクトは見つかりませんでした。" % root))
        return []
    say(_t("Found %d project(s):" % len(projects), "%d 件のプロジェクトを検出しました:" % len(projects)))
    for i, p in enumerate(projects, 1):
        say("  [%d] %-6s %-24s routes~%-3d %s" % (i, p.kind, p.name, p.routes, os.path.relpath(p.path, root) if p.path != os.path.abspath(root) else "."))
    chosen = projects
    if select:
        idx = {int(x) for x in select.split(",") if x.strip().isdigit()}
        chosen = [p for i, p in enumerate(projects, 1) if i in idx]
    elif not assume_yes and len(projects) > 1:
        a = ask(_t("Convert which? (all / numbers like 1,3) [all]: ", "どれを変換しますか? (all / 1,3 のように番号) [all]: ")).strip().lower()
        if a and a != "all":
            idx = {int(x) for x in a.split(",") if x.strip().isdigit()}
            chosen = [p for i, p in enumerate(projects, 1) if i in idx]
    if not chosen:
        say(_t("Nothing selected.", "何も選択されていません。"))
        return []
    out_root = os.path.abspath(out_root or default_out_root(root))
    if not assume_yes and out_root == os.path.abspath(default_out_root(root)):
        a = ask(_t("Destination folder [%s]: " % out_root, "変換先フォルダ [%s]: " % out_root)).strip()
        if a:
            out_root = os.path.abspath(a)
    results = []
    for p in chosen:
        dest = os.path.join(out_root, p.name) if len(chosen) > 1 or not _is_single_file_dest(out_root) else out_root
        if _inside(dest, p.path) and p.kind == "django" and os.path.abspath(dest) == os.path.abspath(p.path):
            say(_t("Skipped %s: destination equals the source." % p.name, "%s をスキップ: 変換先が変換元と同じです。" % p.name))
            continue
        if not os.path.isdir(dest):
            if assume_yes:
                say(_t("Creating %s" % dest, "%s を作成します" % dest))
            else:
                a = ask(_t("Folder does not exist: %s\nCreate it? [Y/n]: " % dest, "フォルダがありません: %s\n作成しますか? [Y/n]: " % dest)).strip().lower()
                if a in ("n", "no", "いいえ"):
                    say(_t("Skipped %s." % p.name, "%s をスキップしました。" % p.name))
                    continue
        elif os.listdir(dest) and not assume_yes:
            a = ask(_t("%s is not empty. Overwrite files with the same name? [y/N]: " % dest, "%s は空ではありません。同名のファイルを上書きしますか? [y/N]: " % dest)).strip().lower()
            if a not in ("y", "yes", "はい"):
                say(_t("Skipped %s." % p.name, "%s をスキップしました。" % p.name))
                continue
        routes, warns = convert_project_to(p, dest, fastapi_version=fastapi_version)
        say(_t("Converted %s -> %s (%d routes, %d warnings)" % (p.name, dest, routes, len(warns)), "変換しました %s -> %s (ルート %d、警告 %d)" % (p.name, dest, routes, len(warns))))
        results.append({"name": p.name, "kind": p.kind, "source": p.path, "dest": dest, "routes": routes, "warnings": warns, "detected": p.detected})
    return results


def _is_single_file_dest(out_root: str) -> bool:
    return False
