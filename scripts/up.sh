#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/source_me.sh"
docker compose -f "${REPO_ROOT}/docker/compose.yaml" up
