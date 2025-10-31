# Label Studio Setup

Simple, self-contained Label Studio setup for defect detection annotation.

## Quick Start

Run Label Studio with a single command:

```bash
docker compose up
```

That's it! The container will:
1. Start Label Studio
2. Wait for it to be ready
3. Automatically create and configure the project
4. Import all tasks from the defect_detect dataset

## Access

Open your browser to: **http://127.0.0.1:8080**

The authentication token is: `label-studio-dev-token-12345`

## Configuration

All configuration is embedded in `compose.yml`. The environment variables are organized as:

**Custom variables (LS_*)** - Used by setup.py:
- `LS_TOKEN` - API authentication token
- `LS_URL` - Label Studio URL
- `LS_PROJECT_NAME` - Project name
- `LS_CONFIG_XML` - Path to label configuration
- `LS_TASKS_JSON` - Path to tasks JSON

**Native variables (LABEL_STUDIO_*)** - Used by Label Studio itself:
- `LABEL_STUDIO_USER_TOKEN` - Authentication token
- `LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN` - Enable API token auth
- `LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED` - Allow local file serving
- `LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT` - Root directory for files

## Data

Images and annotations are mounted from `../data/` directory.

## Stopping

```bash
docker compose down
```

