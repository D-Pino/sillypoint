import argparse
import asyncio
import os
import random
from pathlib import Path

from lxml import etree
import mujoco
import mujoco.viewer
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from thirdman.asset_catalog import load_asset_catalog
from thirdman.common import BASE_SCENE_PATH, GENERATED_SCENES_DIR, GLOBAL_ASSET_STORE


API_KEY = os.getenv("GOOGLE_API_KEY")
SYSTEM_PROMPT = (
    "You output a robot simulation scene as valid MuJoCo XML with root <mujoco>...</mujoco>, no prose.\n"
    "The scene must be a minimal standalone MuJoCo model that parses successfully.\n"
    'Use asset catalog paths exactly as given with <include file="PATH"/> as direct children of <mujoco>, before <worldbody>.\n'
    "Each asset/robot XML file must be included at most once in the entire document: "
    'if you have already used <include file="PATH"/>, never include the same PATH again anywhere.\n'
    "Never put any <include> tag inside <worldbody> or inside any <body>; includes only appear directly under <mujoco>.\n"
    "Correct structure example (do not deviate):\n"
    '<mujoco>\n  <include file="ROBOT_PATH.xml"/>\n  <worldbody>\n    <!-- bodies, geoms, lights, cameras, sites only -->\n  </worldbody>\n</mujoco>\n'
    "Inside <worldbody> use only <body>, <geom>, <light>, <camera>, <site>; do not add other global elements there.\n"
    "Prefer a very simple scene over a complex one; no Markdown, comments, or backticks."
)


def _ensure_unique_path(base_path: Path) -> Path:
    """Return a unique path by appending _1, _2, etc. if the provided path already exists."""
    if not base_path.exists():
        return base_path

    suffix = 1
    while True:
        if base_path.suffix:
            candidate = base_path.with_stem(f"{base_path.stem}_{suffix}")
        else:
            candidate = base_path.with_name(f"{base_path.name}_{suffix}")
        if not candidate.exists():
            return candidate
        suffix += 1


class MujocoSceneDefinition(BaseModel):
    """
    A valid MuJoCo scene definition. This class is used as output type to guide LLM responses with Pydantic AI.
    If validation fails, the request will be retried automatically
    """

    scene_name: str = Field(
        description=("Short, human-readable name for this scene (e.g., 'robot_arena', 'ball_table')")
    )
    scene_definition_xml: str = Field(
        description=(
            "Complete MuJoCo XML for the scene. Must be a standalone <mujoco>...</mujoco> "
            "document that parses successfully in MuJoCo."
        )
    )

    @field_validator("scene_definition_xml")
    @classmethod
    def _validate_scene_definition_xml(cls, v: str) -> str:
        """Basic XML structure validation."""
        root = etree.fromstring(v.encode(encoding="utf-8"))
        if root.tag != "mujoco":
            raise ValueError("Root element must be <mujoco>")
        return v

    @model_validator(mode="after")
    def _validate_mujoco_and_save(self) -> "MujocoSceneDefinition":
        """Validate XML with MuJoCo. We do this more thorough validation in here as opposed to the field_validator
        just so that we can get access to the scene_name so we can easily save and organize validation attempts,
        not for a technical reason"""

        # Use scene name to determine directory for debugging/observability logs
        output_dir = GENERATED_SCENES_DIR / self.scene_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Inject asset directory paths into compiler tag
        root = etree.fromstring(self.scene_definition_xml.encode(encoding="utf-8"))
        compiler = root.find("compiler")
        if compiler is None:
            compiler = etree.Element("compiler")
            root.insert(0, compiler)
        compiler.attrib["meshdir"] = str(GLOBAL_ASSET_STORE)
        compiler.attrib["texturedir"] = str(GLOBAL_ASSET_STORE)
        compiler.attrib["assetdir"] = str(GLOBAL_ASSET_STORE)

        # Get full XML string with compiler paths injected
        full_xml = etree.tostring(root, encoding="utf-8").decode("utf-8")

        # Save this validation attempt
        attempt_dir = _ensure_unique_path(base_path=(output_dir / "validation_attempts" / "attempt"))
        attempt_dir.mkdir(parents=True, exist_ok=True)
        attempt_path = attempt_dir / "scene.xml"
        attempt_path.write_text(data=full_xml, encoding="utf-8")

        # Full MuJoCo validation - if this raises, Pydantic AI will retry
        try:
            mujoco.MjModel.from_xml_string(xml=full_xml)
        except Exception as e:
            error_path = attempt_dir / "error.txt"
            error_path.write_text(data=f"{e.__class__.__name__}: {e}\n", encoding="utf-8")
            raise ValueError(f"MuJoCo validation failed: {e}") from e

        # Update with validated XML
        self.scene_definition_xml = full_xml
        return self


# TEMP: tools disabled for now to avoid extra tool calls while we proof-of-concept
# @dataclass
# class SimGenAgentDeps:
#     catalog: dict[str, dict[str, str]]


# TEMP: tools disabled for now to avoid extra tool calls while we proof-of-concept
# @sim_gen_agent.tool
# def list_assets(ctx: RunContext[SimGenAgentDeps]) -> list[str]:
#     """Return all available asset/robot/model names."""
#     return list(ctx.deps.catalog.keys())


def get_sim_gen_agent() -> Agent:
    provider = GoogleProvider(api_key=API_KEY)
    model = GoogleModel(model_name="gemini-2.0-flash", provider=provider)
    # sim_gen_agent = Agent(
    #     model=model, output_type=MujocoSceneDefinition, system_prompt=SYSTEM_PROMPT, deps_type=SimGenAgentDeps
    # )
    return Agent(
        model=model,
        output_type=MujocoSceneDefinition,
        system_prompt=SYSTEM_PROMPT,
        output_retries=5,
    )


async def generate_mujoco_scene(prompt: str) -> tuple[MujocoSceneDefinition, Path]:
    """Generate a MuJoCo scene and return (scene_definition, scene_root_dir)"""
    # TEMP: no deps / tools; instead, inline a tiny catalog snippet into the prompt
    # TODO: Replace this with tool calls when I have more API calls available to me
    asset_catalog = load_asset_catalog()
    asset_catalog = dict(random.sample(list(asset_catalog.items()), k=min(len(asset_catalog), 10)))
    # Format catalog entries to list only file paths
    asset_catalog_str = "\n".join(record["path"] for record in asset_catalog.values())
    full_prompt = (
        f"{prompt}\n\n"
        "You have access to the following asset file paths. "
        'When you include an asset, use exactly one of these paths in your <include file="..."/> tag. '
        f"{asset_catalog_str}\n\n"
        'Example: If you see "/home/user/robot.xml", write <include file="/home/user/robot.xml"/>'
    )

    sim_gen_agent = get_sim_gen_agent()
    result = await sim_gen_agent.run(user_prompt=full_prompt)
    print(result.usage)

    matching_dirs = list(GENERATED_SCENES_DIR.glob(f"{result.output.scene_name}*"))
    output_dir = (
        max(
            matching_dirs,
            key=lambda p: int(p.name.split("_")[-1]) if p.name.split("_")[-1].isdigit() else 0,
        )
        if matching_dirs
        else GENERATED_SCENES_DIR / result.output.scene_name
    )

    return result.output, output_dir


async def cli():
    parser = argparse.ArgumentParser(description="Generate MuJoCo scene XML from a text description")
    parser.add_argument(
        "prompt",
        help="Description of the scene to generate",
    )
    args = parser.parse_args()

    # Generate the scene
    scene, output_dir = await generate_mujoco_scene(prompt=args.prompt)

    # Write the partial scene (LLM output) into final/
    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    generated_scene_path = final_dir / "generated_scene.xml"
    generated_scene_path.write_text(data=scene.scene_definition_xml, encoding="utf-8")

    # Create the full scene by copying base_scene.xml and adding the include
    base_content = BASE_SCENE_PATH.read_text(encoding="utf-8")
    # Insert the include before the closing </mujoco> tag
    full_scene_content = base_content.replace(
        "</mujoco>", '  <!-- LLM-generated scene included below -->\n  <include file="generated_scene.xml"/>\n</mujoco>'
    )
    full_scene_path = final_dir / "full_scene.xml"
    full_scene_path.write_text(data=full_scene_content, encoding="utf-8")

    # Launch scene
    model = mujoco.MjModel.from_xml_path(str(full_scene_path))
    data = mujoco.MjData(model)
    mujoco.viewer.launch(model, data)


if __name__ == "__main__":
    asyncio.run(cli())
