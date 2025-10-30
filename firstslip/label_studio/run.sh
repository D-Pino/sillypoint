#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
[ -f ../.env ] && source ../.env

export LS_TOKEN="${LS_TOKEN:-$(openssl rand -hex 20)}"

mkdir -p "${LS_DATA_ROOT}" ./project

docker compose -f docker/compose.yml up -d 2>/dev/null

until curl -fsS "${LS_URL}/" >/dev/null 2>&1; do sleep 1; done

python3 setup.py

echo "Open: ${LS_URL}"
