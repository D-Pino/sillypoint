#!/bin/bash

docker compose -f "${REPO_ROOT}/docker/compose.yaml" up db_sillypoint db_odata metabase
