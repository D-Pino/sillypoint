# MuJoCo FastAPI streaming (POC)

Dev run:

1. Export Google key: `export GOOGLE_API_KEY=...`
2. Start FastAPI (port 8010): `uvicorn thirdman.mujoco.app:app --reload --port 8010`
3. Start Django (port 8000):
   - `cd batpad/djbatpad && uv run manage.py runserver 8000`
4. Start React (port 5173):
   - `cd batpad/djbatpad/frontend && yarn dev`
5. Visit `http://localhost:8000/` → redirected to React UI.

Flow:
- React POSTs to `http://localhost:8010/api/generate` with `{ prompt }`
- Response `{ session_id }`
- React opens `ws://localhost:8010/ws/video?session_id=...` and displays JPEG frames.

Notes:
- POC stores generated XML in-memory by `session_id`.
- `thirdman/mujoco/sim.py` can accept XML strings.

