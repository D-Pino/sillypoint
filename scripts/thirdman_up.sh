#!/bin/bash
set -e

# docker compose -f "${REPO_ROOT}/docker/docker-compose.yml" up thirdman

cd "$REPO_ROOT/thirdman"
uv run main.py
