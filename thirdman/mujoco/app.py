import asyncio
import os
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sim import Sim
import uvicorn
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

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


# in-memory store: session_id -> xml
SESSION_XML_STORE: dict[str, str] = {}


def _extract_xml_from_llm_output(text: str) -> str:
    # Strip code fences if present and try to isolate <mujoco>...</mujoco>
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # remove the first fence line and trailing fence
        cleaned = "\n".join([line for line in cleaned.splitlines() if not line.strip().startswith("```")])
        cleaned = cleaned.strip()
    # simple bounds search
    start = cleaned.find("<mujoco")
    end = cleaned.rfind("</mujoco>")
    if start != -1 and end != -1:
        return cleaned[start : end + len("</mujoco>")]
    return cleaned


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not set")

    provider = GoogleProvider(api_key=api_key)
    model = GoogleModel("gemini-2.0-flash", provider=provider)
    agent = Agent(model)

    system_prompt = (
        "You generate valid MuJoCo XML (<mujoco>...</mujoco>). "
        "Return only XML. Provide a minimal but complete scene given the description."
    )
    user_prompt = req.prompt

    result = await agent.run(f"{system_prompt}\nDescription: {user_prompt}")
    xml = _extract_xml_from_llm_output(result.output)

    if "<mujoco" not in xml:
        raise HTTPException(status_code=400, detail="Model generation failed: no <mujoco> tag")

    session_id = str(uuid.uuid4())
    SESSION_XML_STORE[session_id] = xml
    return GenerateResponse(session_id=session_id)


@app.websocket("/ws/video")
async def ws_video(ws: WebSocket, session_id: str = Query(default="")):
    await ws.accept()
    xml = SESSION_XML_STORE.get(session_id)
    if not xml:
        await ws.close(code=1008)
        return
    try:
        sim = Sim(model_xml_str=xml)
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
        sim.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
