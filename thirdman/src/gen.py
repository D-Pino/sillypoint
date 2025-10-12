import argparse
import asyncio
import os
import importlib
import pkgutil
from dataclasses import dataclass

from lxml import etree
import mujoco
from pydantic import BaseModel, field_validator
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
import robot_descriptions


API_KEY = os.getenv("GOOGLE_API_KEY")
SYSTEM_PROMPT = (
    "You output ONLY valid MuJoCo XML (<mujoco>...</mujoco>) with no prose.\n"
    "Goal: given a scene description, produce a minimal but complete scene that represents the description and parses in MuJoCo.\n"
    "Rules:\n"
    '1) Prefer <include file="..."/> using known assets; do not invent paths.\n'
    "2) Always call tool search_assets to find candidates before choosing assets.\n"
    "3) For every chosen name, call resolve_asset and then include_asset_snippet; do not inline large XML.\n"
    "4) If no asset fits, still return a valid empty scene with floor/light/camera.\n"
    "5) No Markdown, no comments, no backticks. Return ONLY the XML string.\n"
)

## TODO: Do some more in depth harvesting of assets from these xmls

# @dataclass
# class RobotBundle:
#     xml_path: Path
#     xml: str
#     assets: dict[str, str]


# def harvest_scene_assets(rd_description_module) -> RobotBundle | None:
#     # TODO: Some of these have URDFS, get those
#     if getattr(rd_description_module, "MJCF_PATH", None) is None:
#         return None
#     robot_xml_path = Path(rd_description_module.MJCF_PATH)
#     robot_tree = mujoco.MjModel.from_xml_path(str(robot_xml_path))
#     robot_xml = robot_tree.to_xml_string().decode("utf-8")
#     assets = dict(robot_tree.get_assets())

#     return RobotBundle(xml_path=robot_xml_path, xml=robot_xml, assets=assets)


def load_rd_assets() -> dict[str, str]:
    robot_assets: dict[str, str] = {}

    # Iterate over the submodules in the robot_descriptions package
    for module_info in pkgutil.iter_modules(robot_descriptions.__path__):
        submodule_name = module_info.name
        if submodule_name.startswith("_") or not submodule_name.endswith(("_mj_description", "_description")):
            continue

        try:
            mod = importlib.import_module(f"robot_descriptions.{submodule_name}")
        except Exception:
            print(f"Error importing {submodule_name}")
            continue

        # Prefer MJCF_PATH if not grab first MJCF_PATH_* that exists and isn't a scene
        xml_path = getattr(mod, "MJCF_PATH", None)
        if xml_path is None:
            continue

        robot_assets[submodule_name] = xml_path

    return dict(sorted(robot_assets.items()))


RD_ASSET_REGISTRY = load_rd_assets()


@dataclass
class SimGenAgentDeps:
    catalog: dict[str, str]


class MujocoSceneDefinition(BaseModel):
    """
    A valid MuJoCo scene definition XML, this class is used as output type to guide LLM responses with Pydantic AI.
    If validation fails, the request will be retried automatically (default Pydantic AI behavior is to retry once)
    """

    scene_definition_xml: str

    @field_validator("scene_definition_xml")
    @classmethod
    def _validate_scene_definition_xml(cls, v: str) -> str:
        # Quick checks to fail fast
        root = etree.fromstring(v.encode("utf-8"))
        if root.tag != "mujoco":
            raise ValueError("Root element must be <mujoco>")

        # Full validation
        mujoco.MjModel.from_xml_string(v)
        return v


provider = GoogleProvider(api_key=API_KEY)
model = GoogleModel(model_name="gemini-2.0-flash", provider=provider)
sim_gen_agent = Agent(
    model=model, output_type=MujocoSceneDefinition, system_prompt=SYSTEM_PROMPT, deps_type=SimGenAgentDeps
)


@sim_gen_agent.tool
def list_assets(ctx: RunContext[SimGenAgentDeps]) -> list[str]:
    """Return all available asset/robot/model names."""
    return sorted(ctx.deps.catalog.keys())


def _norm(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


@sim_gen_agent.tool
def search_assets(ctx: RunContext[SimGenAgentDeps], query: str) -> list[str]:
    """
    Return asset/robot/model names that match the query.
    Ranking: prefix matches first, then substring matches.
    """
    names = sorted(ctx.deps.catalog.keys())
    q = _norm(query)
    pref = [n for n in names if _norm(n).startswith(q)]
    sub = [n for n in names if q in _norm(n) and n not in pref]
    return pref + sub


@sim_gen_agent.tool
def resolve_asset(ctx: RunContext[SimGenAgentDeps], name: str) -> str:
    """Return XML path for an asset/robot/model name."""
    if name not in ctx.deps.catalog:
        raise ValueError(f"unknown asset/robot/model: {name!r}")
    return ctx.deps.catalog[name]


@sim_gen_agent.tool
def include_asset_snippet(ctx: RunContext[SimGenAgentDeps], name: str) -> str:
    """Return <include> tag for an asset/robot/model."""
    return f'<include file="{resolve_asset(ctx, name)}"/>'


async def generate_mujoco_xml(prompt: str) -> str:
    deps = SimGenAgentDeps(catalog=RD_ASSET_REGISTRY)
    result = await sim_gen_agent.run(
        user_prompt=prompt, deps=deps, usage_limits=UsageLimits(tool_calls_limit=5, request_limit=5)
    )
    return result.output.scene_definition_xml


async def cli():
    parser = argparse.ArgumentParser(description="Generate MuJoCo scene XML from a text description")
    parser.add_argument("prompt", help="Description of the scene to generate")
    args = parser.parse_args()

    xml = await generate_mujoco_xml(prompt=args.prompt)
    with open("scene.xml", "w") as f:
        f.write(xml)
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.viewer.launch_passive(model, data)


if __name__ == "__main__":
    asyncio.run(cli())
