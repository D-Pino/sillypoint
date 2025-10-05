# Django + React Setup

## Development Mode

1. **Start the Vite dev server** (in one terminal):
   ```bash
   cd frontend
   yarn install  # first time only
   yarn dev
   ```

2. **Start Django** (in another terminal):
   ```bash
   cd /home/pino/github/sillypoint/batpad/djbatpad
   python manage.py runserver
   ```

3. Visit http://localhost:8000

In dev mode, Vite serves assets with hot module reloading via its dev server on port 5173.

## Production Build

1. **Build the frontend**:
   ```bash
   cd frontend
   yarn build
   ```
   This creates `frontend/dist/` with compiled assets and a manifest.

2. **Run Django**:
   ```bash
   python manage.py runserver
   ```

Django serves the built static files from `frontend/dist/`.

## How It Works

- Django templates extend `base.html` which loads Vite assets via `django-vite`
- React components mount to specific DOM elements by ID
- Props are passed from Django to React via JSON `<script>` tags
- The `main.tsx` file looks for mount points and hydrates them with React components

