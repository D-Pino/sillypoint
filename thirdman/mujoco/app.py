import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sim import Sim
import uvicorn

app = FastAPI()


@app.websocket("/ws/video")
async def ws_video(ws: WebSocket):
    await ws.accept()
    sim = Sim()
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
