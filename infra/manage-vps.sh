#!/usr/bin/env bash
set -euo pipefail

if [[ $# -eq 0 ]]; then
    printf 'Usage: manage-vps.sh <Django management command> [arguments...]\n' >&2
    exit 2
fi

ENV_FILE=/etc/lertix/lertix.env
if [[ ! -r "$ENV_FILE" ]]; then
    printf 'Cannot read environment file: %s\n' "$ENV_FILE" >&2
    exit 1
fi

set -a
. "$ENV_FILE"
set +a

cd /opt/lertix/app/backend
exec /opt/lertix/venv/bin/python manage.py "$@"
