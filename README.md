# 2FastAPI (to FastAPI)

**日本語**: DjangoやFlaskを使ったPythonプログラムを **FastAPI** へ変換するツール(`2` = `to`、`toFastAPI`)。出力は FastAPI と互換のコードで、[MFastAPI](https://github.com/aon-co-jp/MFastAPI)(FastAPI互換を保証)でもそのまま動く想定。コメントと書式は保ったまま書き換える(libcst)。

**English**: Converts Python programs written with **Django or Flask** to **FastAPI** (`2` = `to`). The output is plain FastAPI code that also targets [MFastAPI](https://github.com/aon-co-jp/MFastAPI). Comments and formatting are preserved (libcst). 変換できない部分は黙って壊さず、**警告として報告**する。 / What cannot be converted is reported as a warning, never silently mis-converted.

```
pip install tofastapi           # (またはGitHub Releaseのwheel / or the wheel from the GitHub Release)
2fastapi flask app.py -o app_fastapi.py
2fastapi django path/to/project -o out_dir      # urls.py + views.py -> routers + main.py + CONVERSION_REPORT.md
2fastapi auto <file-or-dir> -o out
uvicorn main:app --reload
```

## 変換するもの / What is converted

| Flask | FastAPI |
|---|---|
| `Flask(__name__)`, `app.run(...)` | `FastAPI()`, `uvicorn.run(app, ...)` |
| `@app.route(rule, methods=[...])`, `@app.get/post/...` | `@app.get/post/...` / `api_route` |
| `<int:id>` `<float:x>` `<path:p>` `<uuid:u>` `<name>` | `{id}` + 型注釈 / `{p:path}` / `uuid.UUID` |
| `request.args.get("q", d, type=int)` / `args["q"]` / `getlist` | クエリパラメータ / query parameters |
| `request.form`, `request.headers`, `request.cookies` | `Form` / `Header` / `Cookie` |
| `request.get_json()` / `request.json` | `payload: Any = Body(None)` |
| `request.method` / `.path` / `.remote_addr` / `url_for` | `Request` 引数 |
| `jsonify(...)`, `return (body, status[, headers])` | dict / `JSONResponse` / `HTMLResponse` |
| `abort(404)`, `redirect(url)` | `HTTPException` / `RedirectResponse(status_code=302)` |
| `Blueprint(url_prefix=)`, `register_blueprint` | `APIRouter(prefix=)`, `include_router` |
| `flask_cors.CORS(app)` | `CORSMiddleware` |
| `@app.before_request` / `after_request` | `@app.middleware("http")` |
| `@app.errorhandler(404)` | `@app.exception_handler(404)` |
| `render_template("x.html", ...)` | `Jinja2Templates.TemplateResponse` |
| `request.files["f"]` (`.read()` `.save()` `.filename`) | `UploadFile` + 同梱の `_Upload` ラッパー / wrapper |
| `flask_restful` `Resource` + `api.add_resource`、`MethodView` + `add_url_rule` | メソッドごとのルート関数 / one route function per method |

| Django | FastAPI |
|---|---|
| `urls.py`: `path()`, `re_path()`, `include()` (入れ子 / nested) | `APIRouter` のパス + `main.py` |
| `<int:pk>` `<slug:s>` `<uuid:u>` `<path:p>`、正規表現の名前付きグループ | `{pk}` + 型注釈(正規表現の制約は外し警告) |
| `request.GET/POST/COOKIES/META/headers`, `getlist` | `Query` / `Form` / `Cookie` / `Header` |
| `JsonResponse`, `HttpResponse`, `HttpResponseRedirect`, `HttpResponseNotFound` 他 | dict / `JSONResponse` / `HTMLResponse` / `RedirectResponse` |
| `raise Http404 / PermissionDenied` | `HTTPException` |
| `@require_GET/POST/http_methods`, `request.method == "POST"` | ルートの HTTP メソッド / route methods |
| `@csrf_exempt` 等 | 削除 / dropped |

## 変換しないもの(警告で報告) / Not converted (reported)
ORM(Django models / Flask-SQLAlchemy)、Djangoのテンプレート(`render`)、セッション/認証(`session`, `flask_login`, `login_required`)、Djangoのクラスベースビュー/DRF、`teardown_request`、`flask.g`、各種 Flask 拡張(`flask_restful`, `flask_jwt_extended` など、手順を警告に表示)。

## 互換性の注意 / Behaviour differences (documented, tested)
- 検証エラー: FastAPI は **422**(Flask/Django の手書き検証や型変換失敗は 400/404)。`<int:id>` に数字以外が来たとき Flask は 404、FastAPI は 422。
- リクエスト値は文字列のまま(`request.args.get("n", 10)` は `str`)。`type=int` のときだけ型付き。Django の `re_path` グループは `str`。
- `jsonify` と dict 返却は JSON。文字列返却は `HTMLResponse`(Flask と同じ text/html)。
- 末尾スラッシュ: 宣言どおり。FastAPI は不一致を 307 でリダイレクト(Flask は 308、Django は 301)。

テストは **Flask / Django の元アプリと変換後の FastAPI アプリへ同じリクエストを投げて、ステータスと本文を比較**する差分テスト(`tests/`)。 / Tests send identical requests to the original Flask/Django app and the converted FastAPI app and compare status and body.

## 開発 / Development
```
bash setup-wsl.sh        # WSL: uv で検証用 venv を作成 / creates a test venv
bash run-tests.sh        # pytest
```
CI は Ubuntu / Windows / macOS × Python 3.10・3.12・3.13。 / ライセンス: MIT
