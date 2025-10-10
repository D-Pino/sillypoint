import argparse
import asyncio
import os

from lxml import etree
import mujoco
from pydantic import BaseModel, field_validator
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider


API_KEY = os.getenv("GOOGLE_API_KEY")
SYSTEM_PROMPT = (
    "You generate valid MuJoCo XML (<mujoco>...</mujoco>). "
    "Return only XML. Provide a minimal but complete scene given the description."
)


class MujocoSceneDefinition(BaseModel):
    """
    A valid MuJoCo scene definition XML, used as output type to guide LLM responses with Pydantic AI.
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


async def generate_mujoco_xml(prompt: str) -> str:
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not set")

    provider = GoogleProvider(api_key=API_KEY)
    model = GoogleModel(model_name="gemini-2.0-flash", provider=provider)
    agent = Agent(model=model, output_type=MujocoSceneDefinition, system_prompt=SYSTEM_PROMPT)

    result = await agent.run(prompt)
    return result.output.scene_definition_xml


async def cli():
    parser = argparse.ArgumentParser(description="Generate MuJoCo scene XML from a text description")
    parser.add_argument("prompt", help="Description of the scene to generate")
    args = parser.parse_args()

    xml = await generate_mujoco_xml(prompt=args.prompt)
    print(xml)


if __name__ == "__main__":
    asyncio.run(cli())
