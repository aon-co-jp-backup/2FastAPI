# 2FastAPI PORTING / 再開メモ

## 日本語
**状態**: v0.2.0+。Flask(フック・render_template・request.files・Flask-RESTful/MethodView)とDjango(View継承クラス)をFastAPIへ変換。scan/auto/convertで複数プロジェクトを自動検出し、変換先を英日で質問(無ければ作成確認)。差分テスト36件、CIは3OS成功。
**未了**: Django TemplateView/DRF、Flask-SQLAlchemy/marshmallow/JWTの組み合わせ、PyPI公開、Python 3.14ネイティブのlibcst(WindowsのPythonにlibcst無し→テストはWSL)。
**再開用メッセージ**: 「`F:\runo\PORTING.md` 末尾の「2026-11-15 別アカウントでの再開用メモ」と、`F:$1\PORTING.md` を読んで、未了の続きを確認なしで開発・TEST・DEBUG・commit・pushして。チャットは日本語のみ。」
**テスト**: WSL: powershell -c "wsl -d Ubuntu -- bash /mnt/f/2FastAPI/run-tests.sh" (setup-wsl.sh で環境作成 / creates the env; TAILN=100 で出力を増やす / more output)

## English
**Status**: v0.2.0+. Converts Flask (hooks, render_template, request.files, Flask-RESTful/MethodView) and Django (View subclasses) to FastAPI. scan/auto/convert detect several projects and ask in English and Japanese where to put the result (creating folders). 36 differential tests, CI green on 3 OSes.
**Open**: Django TemplateView/DRF, Flask-SQLAlchemy/marshmallow/JWT combinations, PyPI publication, libcst on native Windows Python 3.14 (tests run in WSL).
**Resume message**: "Read the 2026-11-15 section at the end of `F:\runo\PORTING.md` and `F:$1\PORTING.md`, then continue the open items without asking (develop, test, debug, commit, push). Chat in Japanese only."
**Tests**: WSL: powershell -c "wsl -d Ubuntu -- bash /mnt/f/2FastAPI/run-tests.sh" (setup-wsl.sh で環境作成 / creates the env; TAILN=100 で出力を増やす / more output)
