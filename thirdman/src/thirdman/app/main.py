import asyncio
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from thirdman.sim import Sim, SimConfig
from thirdman.gen import generate_mujoco_xml

app = FastAPI()

# CORS for Django (8000) and Vite (5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    session_id: str
    scene_xml: str

# in-memory store: session_id -> xml
SESSION_XML_STORE: dict[str, str] = {}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    xml = await generate_mujoco_xml(prompt=req.prompt)
    session_id = str(uuid.uuid4())
    SESSION_XML_STORE[session_id] = xml
    return GenerateResponse(session_id=session_id, scene_xml=xml)


@app.websocket("/ws/video")
async def ws_video(ws: WebSocket, session_id: str = Query(default="")):
    await ws.accept()
    xml = SESSION_XML_STORE.get(session_id)
    if not xml:
        await ws.close(code=1008)
        return
    try:
        sim = Sim(cfg=SimConfig(scene_xml=xml))
    except Exception:
        await ws.close(code=1011)
        return
    try:
        while True:
            jpeg = sim.next_frame_jpeg()
            await ws.send_bytes(jpeg)
            await asyncio.sleep(1 / 24)
    except WebSocketDisconnect:
        pass
    finally:
        # sim.close()
        pass

