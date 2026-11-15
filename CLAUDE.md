# 2FastAPI 開発方針 / Development notes

**日本語**: 共通ルールは [`open-raid-z/CLAUDE.md`](https://github.com/aon-co-jp/open-raid-z) と [`runo`](https://github.com/aon-co-jp/runo) の `CLAUDE.md` を参照。チャットは日本語のみ。確認なしで開発・TEST・DEBUG・commit・push。UI・インストーラーはリリース前に実機/エミュレーターで確認。heredocでバックスラッシュを含むコードを書かない(Writeツールを使う)。
**English**: shared rules live in `open-raid-z/CLAUDE.md` and `runo/CLAUDE.md`. Chat in Japanese only. Develop, test, debug, commit and push without asking. Verify UI/installers on real devices/emulators before each release. Do not write code containing backslashes through bash heredocs (use the Write tool).

## 状態 / Status
- 日本語: v0.2.0+。Flask(フック・render_template・request.files・Flask-RESTful/MethodView)とDjango(View継承クラス)をFastAPIへ変換。scan/auto/convertで複数プロジェクトを自動検出し、変換先を英日で質問(無ければ作成確認)。差分テスト36件、CIは3OS成功。
- English: v0.2.0+. Converts Flask (hooks, render_template, request.files, Flask-RESTful/MethodView) and Django (View subclasses) to FastAPI. scan/auto/convert detect several projects and ask in English and Japanese where to put the result (creating folders). 36 differential tests, CI green on 3 OSes.

## 未了 / Open
- 日本語: Django TemplateView/DRF、Flask-SQLAlchemy/marshmallow/JWTの組み合わせ、PyPI公開、Python 3.14ネイティブのlibcst(WindowsのPythonにlibcst無し→テストはWSL)。
- English: Django TemplateView/DRF, Flask-SQLAlchemy/marshmallow/JWT combinations, PyPI publication, libcst on native Windows Python 3.14 (tests run in WSL).

詳細・再開用メッセージ / details and the resume message: [`PORTING.md`](PORTING.md)
