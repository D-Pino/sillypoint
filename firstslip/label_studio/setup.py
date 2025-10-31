#!/usr/bin/env python3
import json
import os
from pathlib import Path
from label_studio_sdk import LabelStudio

BASE_URL = os.getenv("LS_URL")
API_KEY = os.getenv("LS_TOKEN")
PROJECT_TITLE = os.getenv("LS_PROJECT_NAME")
CONFIG_XML_PATH = Path(os.getenv("LS_CONFIG_XML"))
TASKS_JSON_PATH = Path(os.getenv("LS_TASKS_JSON"))

client = LabelStudio(base_url=BASE_URL, api_key=API_KEY)

label_config = CONFIG_XML_PATH.read_text(encoding="utf-8")
project = client.projects.create(title=PROJECT_TITLE, label_config=label_config)

tasks = json.loads(TASKS_JSON_PATH.read_text(encoding="utf-8"))
client.projects.import_tasks(id=project.id, request=tasks)

print(f"Ready: {BASE_URL}/projects/{project.id}/data")
