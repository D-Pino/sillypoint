# Bootstrap Documentation

This document outlines the steps taken to create this Django + React project from scratch.

## Django Setup

1. **Create the Django project:**
   ```bash
   django-admin startproject djbatpad
   cd djbatpad
   ```

2. **Create a Django app:**
   ```bash
   python manage.py startapp robots
   ```


## Frontend Setup

1. **Install Yarn** (if not already installed):
   ```bash
   npm install -g yarn
   ```

2. **Create Vite React project:**
   ```bash
   yarn create vite frontend --template react-ts
   cd frontend
   yarn install
   ```

3. **Configure React mounting:**
   - Modified `main.tsx` to look for mount points by ID
   - Set up dynamic component mounting to connect Django URLs with React frontends
   - Components mount to specific DOM elements rendered by Django templates

4. **Add Mantine for styling:**
   ```bash
   yarn add @mantine/core @mantine/hooks
   yarn add -D postcss postcss-preset-mantine postcss-simple-vars
   ```

5. **Create PostCSS configuration:**
   - Created `postcss.config.cjs` file
   - Configured Mantine presets and PostCSS plugins

## Integration

The project uses `django-vite` to integrate the React frontend with Django:
- In development: Vite dev server runs on port 5173 with HMR
- In production: Django serves built static files from `frontend/dist/`
- Props are passed from Django templates to React via JSON script tags
- See `SETUP.md` for development and deployment instructions

