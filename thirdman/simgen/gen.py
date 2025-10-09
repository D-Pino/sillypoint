import os

from fastapi import HTTPException
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider


API_KEY = os.getenv("GOOGLE_API_KEY")


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


async def generate_mujoco_xml(prompt: str) -> str:
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not set")

    provider = GoogleProvider(api_key=API_KEY)
    model = GoogleModel("gemini-2.0-flash", provider=provider)
    agent = Agent(model)

    system_prompt = (
        "You generate valid MuJoCo XML (<mujoco>...</mujoco>). "
        "Return only XML. Provide a minimal but complete scene given the description."
    )
    user_prompt = prompt

    result = await agent.run(f"{system_prompt}\nDescription: {user_prompt}")
    xml = _extract_xml_from_llm_output(result.output)

    if "<mujoco" not in xml:
        raise HTTPException(status_code=400, detail="Model generation failed: no <mujoco> tag")

    return xml
