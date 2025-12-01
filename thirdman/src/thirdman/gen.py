import argparse
import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from lxml import etree
import mujoco
import mujoco.viewer
from pydantic import BaseModel, field_validator
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from thirdman.asset_catalog import load_asset_catalog


API_KEY = os.getenv("GOOGLE_API_KEY")
SYSTEM_PROMPT = (
    "You output ONLY valid MuJoCo XML (<mujoco>...</mujoco>) with no prose.\n"
    "Goal: given a scene description, produce a minimal but complete scene that follows the description and parses in MuJoCo.\n"
    "\n"
    "Overall structure:\n"
    '- The root element must be <mujoco model="scene"> (or another short model name).\n'
    "- Direct children of <mujoco> may include:\n"
    "  - One or more <include> elements for external MJCF assets.\n"
    "  - Exactly one <worldbody> element defining the main scene bodies/geoms/lights/cameras.\n"
    "- Never put <include> inside <worldbody> or inside any <body>.\n"
    "\n"
    "Asset catalog in the user prompt:\n"
    "- The user prompt may contain a small catalog of asset names and file paths.\n"
    "- When you decide to use an asset from that catalog, insert a line like:\n"
    '    <include file="FULL_PATH_FROM_CATALOG"/>\n'
    "  as a direct child of <mujoco>, BEFORE <worldbody>.\n"
    "- Do NOT invent or modify paths; use them exactly as given.\n"
    "\n"
    "Inside <worldbody>:\n"
    "- You may ONLY use elements allowed there: <body>, <geom>, <light>, <camera>, <site>.\n"
    "- Do NOT use <compiler>, <option>, <default>, <size>, additional <mujoco>, or additional <worldbody> elements anywhere inside <worldbody>.\n"
    "- Keep the scene simple: a ground plane, at most a few bodies, one light, and an optional camera.\n"
    "\n"
    "General rules:\n"
    "- Prefer a very simple, robustly valid scene over a complex one.\n"
    "- No Markdown, no comments, no backticks; return ONLY the XML string.\n"
)


class MujocoSceneDefinition(BaseModel):
    """
    A valid MuJoCo scene definition XML, this class is used as output type to guide LLM responses with Pydantic AI.
    If validation fails, the request will be retried automatically (default Pydantic AI behavior is to retry once)
    """

    scene_definition_xml: str

    @field_validator("scene_definition_xml")
    @classmethod
    def _validate_scene_definition_xml(cls, v: str) -> str:
        # Temp, just for debugging. TODO: remove
        filename = f"candidate_scene_{datetime.now().strftime('%Y%m%d%H%M%S')}.xml"
        # Write candidate scenes to the top-level thirdman/candidate_scenes directory
        output_dir = Path(__file__).resolve().parents[2] / "candidate_scenes"
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / filename).open(mode="w") as f:
            f.write(v)

        # Quick checks to fail fast
        root = etree.fromstring(v.encode("utf-8"))
        if root.tag != "mujoco":
            raise ValueError("Root element must be <mujoco>")

        # Full validation
        mujoco.MjModel.from_xml_string(v)
        return v


@dataclass
class SimGenAgentDeps:
    catalog: dict[str, dict[str, str]]


# TEMP: tools disabled for now to avoid extra tool calls while we proof-of-concept
# @sim_gen_agent.tool
# def list_assets(ctx: RunContext[SimGenAgentDeps]) -> list[str]:
#     """Return all available asset/robot/model names."""
#     return list(ctx.deps.catalog.keys())


# @sim_gen_agent.tool
# def get_asset_path(ctx: RunContext[SimGenAgentDeps], name: str) -> str:
#     """Return the path for an asset/robot/model name."""
#     return ctx.deps.catalog[name]


# def _norm(s: str) -> str:
#     return "".join(ch for ch in s.lower() if ch.isalnum())


# @sim_gen_agent.tool
# def search_assets(ctx: RunContext[SimGenAgentDeps], query: str) -> list[str]:
#     """
#     Return asset/robot/model names that match the query.
#     Ranking: prefix matches first, then substring matches.
#     """
#     names = sorted(ctx.deps.catalog.keys())
#     q = _norm(query)
#     pref = [n for n in names if _norm(n).startswith(q)]
#     sub = [n for n in names if q in _norm(n) and n not in pref]
#     return pref + sub


# @sim_gen_agent.tool
# def resolve_asset(ctx: RunContext[SimGenAgentDeps], name: str) -> str:
#     """Return XML path for an asset/robot/model name."""
#     if name not in ctx.deps.catalog:
#         raise ValueError(f"unknown asset/robot/model: {name!r}")
#     return ctx.deps.catalog[name]


# @sim_gen_agent.tool
# def include_asset_snippet(ctx: RunContext[SimGenAgentDeps], name: str) -> str:
#     """Return <include> tag for an asset/robot/model."""
#     return f'<include file="{resolve_asset(ctx, name)}"/>'


provider = GoogleProvider(api_key=API_KEY)
model = GoogleModel(model_name="gemini-2.0-flash", provider=provider)
# sim_gen_agent = Agent(
#     model=model, output_type=MujocoSceneDefinition, system_prompt=SYSTEM_PROMPT, deps_type=SimGenAgentDeps
# )
sim_gen_agent = Agent(
    model=model,
    output_type=MujocoSceneDefinition,
    system_prompt=SYSTEM_PROMPT,
    output_retries=3,
)


async def generate_mujoco_xml(prompt: str) -> str:
    # TEMP: no deps / tools; instead, inline a tiny catalog snippet into the prompt
    asset_catalog = load_asset_catalog()
    asset_catalog = dict(list(asset_catalog.items())[:10])
    
    # Paths are now absolute, use them directly
    asset_catalog_str = "\n".join(
        f"- {name}: {record['path']} ({record['match_substring']})" 
        for name, record in asset_catalog.items()
    )
    full_prompt = (
        f"{prompt}\n\n"
        "You have access to the following small asset catalog. "
        'When you include an asset, insert <include file="PATH"/> as a direct child of <mujoco>, '
        "using the PATH exactly as given:\n"
        f"{asset_catalog_str}"
    )
    result = await sim_gen_agent.run(
        user_prompt=full_prompt,
        usage_limits=UsageLimits(tool_calls_limit=10, request_limit=10),
    )
    return result.output.scene_definition_xml


async def cli():
    parser = argparse.ArgumentParser(description="Generate MuJoCo scene XML from a text description")
    parser.add_argument(
        "prompt", default="A simple scene with a table and a chair", help="Description of the scene to generate"
    )
    args = parser.parse_args()

    xml = await generate_mujoco_xml(prompt=args.prompt)
    with open("scene.xml", "w") as f:
        f.write(xml)
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.viewer.launch(model, data)


if __name__ == "__main__":
    asyncio.run(cli())
