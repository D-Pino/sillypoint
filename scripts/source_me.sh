#!/bin/bash
set -a

REPO_ROOT=$(git rev-parse --show-toplevel)
ENV_FILE="$REPO_ROOT/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: .env file not found at $ENV_FILE"
    return 1
fi

source "$ENV_FILE"

# Add repo root to PYTHONPATH so cowcorner package can be imported
export PYTHONPATH="$REPO_ROOT:$PYTHONPATH"

set +a
