#!/bin/bash

docker compose -f "${REPO_ROOT}/docker/docker-compose.yml" up db metabase
