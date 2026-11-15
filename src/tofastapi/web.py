# -*- coding: utf-8 -*-
"""2FastAPI browser wizard: the same steps as the GUI, served only on this PC (127.0.0.1) so it can run on open-easy-web or alone.

API: Connect unary calls  POST /tofastapi.v1.Wizard/<ListDir|Scan|Convert>  (JSON). No REST routes; GET / serves the page.
Safety: loopback only, a random per-run token, Host header check (DNS rebinding), directories only, 1 MB request limit.
"""
from __future__ import annotations

import json
import os
import secrets
import string
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from . import __version__
from .i18n import LANGS, S

PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>2FastAPI</title><style>
:root{--bg:#fff;--fg:#14181f;--sub:#57606a;--card:#f6f8fa;--line:#d0d7de;--acc:#1f6feb}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--sub:#8b949e;--card:#161b22;--line:#30363d;--acc:#4a9eff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,'Segoe UI','Noto Sans',sans-serif}
main{max-width:820px;margin:0 auto;padding:16px 16px 96px}h1{font-size:1.5rem;margin:6px 0}
.q{white-space:pre-line;margin:10px 0;font-size:1.05rem}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin:10px 0}
button,select,input[type=text]{font:inherit;padding:8px 12px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg)}
button.p{background:var(--acc);color:#fff;border-color:var(--acc)}.dir{display:block;width:100%;text-align:start;margin:2px 0}
.nav{position:fixed;inset:auto 0 0 0;background:var(--bg);border-top:1px solid var(--line);padding:10px 16px;display:flex;gap:8px;justify-content:space-between}
.path{width:100%}label{display:block;margin:6px 0}
</style></head><body><main><h1>2FastAPI</h1>
<div><span id="lbl"></span> <select id="lang"></select></div>
<div id="view"></div></main><div class="nav" id="nav"></div>
<script>
const TOKEN="__TOKEN__",S=__S__,LANGS=__LANGS__;let L="default",page=0,src="",dst="",projects=[],picked=[],target="fastapi",res=null;
const t=(k,v)=>{const f=l=>(S[l][k]||"").replace(/\{(\w+)\}/g,(m,x)=>v&&x in v?v[x]:m);if(L==="default"){const a=f("en"),b=f("ja");return a===b?a:a+"\n"+b}return f(L)};
const $=id=>document.getElementById(id);
async function rpc(m,b){const r=await fetch("/tofastapi.v1.Wizard/"+m,{method:"POST",headers:{"content-type":"application/json","x-token":TOKEN},body:JSON.stringify(b||{})});const j=await r.json();if(!r.ok)throw new Error(j.message||r.status);return j}
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function btn(txt,cls,fn){const b=document.createElement("button");b.textContent=txt;if(cls)b.className=cls;b.onclick=fn;return b}
function picker(key){const box=document.createElement("div");box.className="card";const inp=document.createElement("input");inp.type="text";inp.className="path";inp.value=key==="src"?src:dst;inp.oninput=()=>{key==="src"?src=inp.value:dst=inp.value};box.appendChild(inp);const list=document.createElement("div");box.appendChild(list);
 async function ls(p){try{const j=await rpc("ListDir",{path:p});inp.value=j.path;key==="src"?src=j.path:dst=j.path;list.innerHTML="";if(j.parent)list.appendChild(btn("↑ ..","dir",()=>ls(j.parent)));j.dirs.forEach(d=>list.appendChild(btn("📁 "+d.name,"dir",()=>ls(d.path))))}catch(e){list.textContent=e.message}}
 const go=btn(t("browse"),"",()=>ls(inp.value));box.insertBefore(go,list);ls(inp.value||"");return box}
function render(){document.documentElement.dir=LANGS.find(x=>x[0]===L)[2];$("lbl").textContent=t("language");const v=$("view"),nav=$("nav");v.innerHTML="";nav.innerHTML="";const q=x=>{const d=document.createElement("div");d.className="q";d.textContent=x;v.appendChild(d)};
 if(page===0){q(t("q_src"));v.appendChild(picker("src"));nav.append(document.createElement("span"),btn(t("next"),"p",scan))}
 else if(page===1){q(projects.length?t("found",{n:projects.length}):t("none"));projects.forEach((p,i)=>{const l=document.createElement("label");l.innerHTML='<input type="checkbox" '+(picked[i]?"checked":"")+'> '+esc(p.name)+" ["+esc(p.kind)+"] ~"+p.routes+" routes "+esc(p.path);l.firstChild.onchange=e=>picked[i]=e.target.checked;v.appendChild(l)});nav.append(btn(t("back"),"",()=>{page=0;render()}),projects.length?btn(t("next"),"p",()=>{if(!picked.some(Boolean)){alert(t("nosel"));return}if(!dst)dst=src.replace(/[\\/]+$/,"")+"-fastapi";page=2;render()}):document.createElement("span"))}
 else if(page===2){q(t("q_dst"));v.appendChild(picker("dst"));const h=document.createElement("div");h.className="q";h.textContent=t("q_target");v.appendChild(h);[["fastapi","t_fastapi"],["mfastapi","t_mfastapi"]].forEach(([val,k])=>{const l=document.createElement("label");l.innerHTML='<input type="radio" name="tg" '+(target===val?"checked":"")+'> '+esc(t(k));l.firstChild.onchange=()=>target=val;v.appendChild(l)});nav.append(btn(t("back"),"",()=>{page=1;render()}),btn(t("convert"),"p",convert))}
 else{q(res.err?t("err")+": "+res.err:t("done",{n:res.n,w:res.w}));nav.append(document.createElement("span"),btn(t("close"),"p",()=>{page=0;render()}))}}
async function scan(){if(!src){alert(t("q_src"));return}try{const j=await rpc("Scan",{path:src});projects=j.projects;picked=projects.map(()=>true);dst="";page=1;render()}catch(e){alert(e.message)}}
async function convert(){if(!dst){alert(t("nodst"));return}try{res=await rpc("Convert",{path:src,dest:dst,target,names:projects.filter((p,i)=>picked[i]).map(p=>p.path)})}catch(e){res={n:0,w:0,err:e.message}}page=3;render()}
const sel=$("lang");LANGS.forEach(x=>{const o=document.createElement("option");o.value=x[0];o.textContent=x[1];sel.appendChild(o)});sel.onchange=()=>{L=sel.value;render()};render();
</script></body></html>"""


def _roots():
    if os.name == "nt":
        return ["%s:\\" % c for c in string.ascii_uppercase if os.path.isdir("%s:\\" % c)]
    return ["/"]


class _Handler(BaseHTTPRequestHandler):
    server_version = "2FastAPI"
    token = ""
    port = 0

    def log_message(self, *a):  # quiet
        pass

    def _host_ok(self) -> bool:
        return (self.headers.get("Host") or "") in ("127.0.0.1:%d" % self.port, "localhost:%d" % self.port)

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(body)))
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.send_header("content-security-policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: Dict[str, Any]):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"code": "permission_denied", "message": "bad host"})
        if self.path.split("?")[0] == "/":
            page = PAGE.replace("__TOKEN__", self.token).replace("__S__", json.dumps(S, ensure_ascii=False)).replace("__LANGS__", json.dumps(LANGS, ensure_ascii=False))
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        if self.path == "/healthz":
            return self._send(200, b"ok", "text/plain")
        self._json(404, {"code": "not_found", "message": "not found"})

    def do_POST(self):
        if not self._host_ok() or not secrets.compare_digest(self.headers.get("x-token", ""), self.token):
            return self._json(403, {"code": "permission_denied", "message": "forbidden"})
        pre = "/tofastapi.v1.Wizard/"
        if not self.path.startswith(pre):
            return self._json(404, {"code": "not_found", "message": "not found"})
        try:
            n = int(self.headers.get("content-length") or 0)
            if n > 1_000_000:
                return self._json(400, {"code": "invalid_argument", "message": "too large"})
            req = json.loads(self.rfile.read(n) or b"{}")
            method = self.path[len(pre):]
            if method == "ListDir":
                return self._json(200, self._list_dir(str(req.get("path") or "")))
            if method == "Scan":
                from .scan import scan

                d = os.path.abspath(str(req.get("path") or ""))
                if not os.path.isdir(d):
                    return self._json(400, {"code": "invalid_argument", "message": "not a folder"})
                return self._json(200, {"projects": [p.to_dict() for p in scan(d)]})
            if method == "Convert":
                from .scan import convert_project_to, scan

                src = os.path.abspath(str(req.get("path") or ""))
                dst = os.path.abspath(str(req.get("dest") or ""))
                if not os.path.isdir(src) or not dst or dst == src:
                    return self._json(400, {"code": "invalid_argument", "message": "bad source or destination"})
                want = {os.path.abspath(x) for x in req.get("names") or []}
                target = "mfastapi" if req.get("target") == "mfastapi" else "fastapi"
                chosen = [p for p in scan(src) if os.path.abspath(p.path) in want]
                nn = ww = 0
                for p in chosen:
                    out = os.path.join(dst, p.name) if len(chosen) > 1 else dst
                    _, warns = convert_project_to(p, out, target)
                    nn += 1
                    ww += len(warns)
                return self._json(200, {"n": nn, "w": ww, "dest": dst})
            return self._json(404, {"code": "unimplemented", "message": method})
        except ImportError:
            return self._json(500, {"code": "internal", "message": "conversion library (libcst) is missing"})
        except Exception as e:
            return self._json(500, {"code": "internal", "message": "%s: %s" % (type(e).__name__, e)})

    @staticmethod
    def _list_dir(path: str) -> Dict[str, Any]:
        if not path:
            home = os.path.expanduser("~")
            path = home if os.path.isdir(home) else _roots()[0]
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise ValueError("not a folder")
        parent = os.path.dirname(path)
        dirs = []
        try:
            for name in sorted(os.listdir(path), key=str.lower):
                full = os.path.join(path, name)
                if os.path.isdir(full) and not name.startswith("."):
                    dirs.append({"name": name, "path": full})
        except PermissionError:
            pass
        return {"path": path, "parent": parent if parent != path else "", "dirs": dirs[:500]}


def serve(open_browser: bool = True, port: int = 0) -> int:
    token = secrets.token_urlsafe(24)
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    _Handler.token = token
    _Handler.port = srv.server_address[1]
    url = "http://127.0.0.1:%d/" % _Handler.port
    print("2FastAPI %s web wizard: %s  (Ctrl+C to stop / 停止は Ctrl+C)" % (__version__, url))
    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(serve())
