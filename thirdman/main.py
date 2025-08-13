import os
import mujoco
from mujoco import viewer

REPO_ROOT = os.environ.get("REPO_ROOT", "..")

with open(f"{REPO_ROOT}/thirdman/humanoid_with_conveyor.xml", "r") as f:
    xml = f.read()
model = mujoco.MjModel.from_xml_string(xml)
scene_option = mujoco.MjvOption()
scene_option.flags[mujoco.mjtVisFlag.mjVIS_JOINT] = True

# data = mujoco.MjData(model)
# with mujoco.Renderer(model) as renderer:
#     mujoco.mj_forward(model, data)
#     renderer.update_scene(data)

#     idk = renderer.render()
#     print(idk)


if __name__ == "__main__":
    viewer.launch(model)
