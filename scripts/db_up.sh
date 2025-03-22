#!/bin/bash

docker compose -f "${REPO_ROOT}/docker/docker-compose.yml" up db_sillypoint db_odata metabase
