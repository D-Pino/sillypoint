#!/usr/bin/env python3
import json
import os
from pathlib import Path
from label_studio_sdk import LabelStudio

BASE_URL = "http://127.0.0.1:8080"
API_KEY = os.getenv("LS_TOKEN")
PROJECT_TITLE = os.getenv("LABEL_STUDIO_PROJECT_NAME")
CONFIG_XML_PATH = Path(os.getenv("LABEL_STUDIO_CONFIG_XML"))
TASKS_JSON_PATH = Path(os.getenv("LABEL_STUDIO_TASKS_JSON"))
HOST_DATA_ROOT = Path(os.getenv("LABEL_STUDIO_DATA_ROOT"))

client = LabelStudio(base_url=BASE_URL, api_key=API_KEY)


DATA_KEY = os.getenv("LABEL_STUDIO_DATA_KEY", "image")


def normalize_tasks(raw):
    items = raw if isinstance(raw, list) else [raw]
    out = []
    for t in items:
        data = dict(t.get("data", t))
        v = data.get(DATA_KEY)
        if v and isinstance(v, str) and not v.startswith("/data/local-files/?d="):
            rel = Path(v).resolve().relative_to(HOST_DATA_ROOT.resolve())
            data[DATA_KEY] = f"/data/local-files/?d={rel.as_posix()}"
        out.append({"data": data})
    return out


label_config = CONFIG_XML_PATH.read_text(encoding="utf-8")
project = client.projects.create(title=PROJECT_TITLE, label_config=label_config)

tasks = normalize_tasks(json.loads(TASKS_JSON_PATH.read_text(encoding="utf-8")))
payload = [t["data"] for t in tasks]
client.projects.import_tasks(id=project.id, request=payload)

print(f"Ready: {BASE_URL}/projects/{project.id}/data")
