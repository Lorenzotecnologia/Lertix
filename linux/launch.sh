#!/usr/bin/env bash
set -euo pipefail

PACKAGE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PACKAGE_DIR/backend"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="$PACKAGE_DIR/.venv"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python 3.12 ou superior não foi encontrado (comando: $PYTHON_BIN)." >&2
    exit 1
fi

if ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
    echo "Python 3.12 ou superior é necessário para executar o Lertix." >&2
    exit 1
fi

if [[ ! -f "$VENV_DIR/.lertix-dependencies-installed" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"
    touch "$VENV_DIR/.lertix-dependencies-installed"
fi

HOST="${LERTIX_HOST:-127.0.0.1}"
PORT="${LERTIX_PORT:-8000}"
cd "$BACKEND_DIR"
exec "$VENV_DIR/bin/python" manage.py runserver "$HOST:$PORT"
