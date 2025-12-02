# from dataclasses import dataclass
import time
import io

import numpy as np
import mujoco
from pathlib import Path

from PIL import Image
from pydantic import BaseModel

from thirdman.common import BASE_SCENE_PATH


class SimConfig(BaseModel):
    scene_xml: Path | str = BASE_SCENE_PATH


class Sim:
    def __init__(self, cfg: SimConfig | None = None):
        self.cfg = cfg or SimConfig()

        if isinstance(self.cfg.scene_xml, str):
            self.model = mujoco.MjModel.from_xml_string(self.cfg.scene_xml)
        else:
            self.model = mujoco.MjModel.from_xml_path(str(self.cfg.scene_xml))

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
        self.step(n=1)
        rgb = self.render_rgb()
        return self.encode_jpeg(img_rgb=rgb)
