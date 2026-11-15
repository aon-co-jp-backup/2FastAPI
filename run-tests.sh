#!/usr/bin/env bash
# usage: run-tests.sh [pytest args...]   (WSL; env created by setup-wsl.sh)
export PATH="$HOME/.local/bin:/usr/bin:/bin"
. "$HOME/2fa-venv/bin/activate"
cd "$(dirname "$0")"
export PYTHONPATH="$PWD/src:$PWD/tests"
python -m pytest -q -p no:cacheprovider "$@" 2>&1 | tail -${TAILN:-40}
