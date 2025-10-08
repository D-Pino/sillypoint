import time
import io

import numpy as np
import mujoco
from pathlib import Path

from PIL import Image
from pydantic import BaseModel


class SimConfig(BaseModel):
    width: int = 640
    height: int = 360
    model_xml_path: Path = Path(__file__).parent / "humanoid_with_conveyor.xml"


class Sim:
    def __init__(self, cfg: SimConfig | None = None, model_xml_str: str | None = None):
        self.cfg = cfg or SimConfig()

        if model_xml_str is not None:
            self.model = mujoco.MjModel.from_xml_string(model_xml_str)
        else:
            self.model = mujoco.MjModel.from_xml_path(str(self.cfg.model_xml_path))
        self.data = mujoco.MjData(self.model)
        self.renderer = mujoco.Renderer(self.model)

        # Simple fixed camera
        self.cam = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(self.cam)
        self.cam.lookat[:] = (0, 0, 0.8)
        self.cam.distance = 2.0
        self.cam.elevation = -20.0
        self.cam.azimuth = 90.0

        self._next_t = time.perf_counter()

    def step(self, n: int) -> None:
        for _ in range(n):
            mujoco.mj_step(self.model, self.data)

    def render_rgb(self) -> np.ndarray:
        self.renderer.update_scene(self.data, camera=self.cam)
        return self.renderer.render()  # HxWx3 uint8 RGB

    @staticmethod
    def encode_jpeg(img_rgb: np.ndarray, quality: int = 80) -> bytes:
        buf = io.BytesIO()
        Image.fromarray(img_rgb, mode="RGB").save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()

    def next_frame_jpeg(self) -> bytes:
        self.step(1)
        rgb = self.render_rgb()
        return self.encode_jpeg(rgb, 80)

    def close(self) -> None:
        self.renderer.close()
