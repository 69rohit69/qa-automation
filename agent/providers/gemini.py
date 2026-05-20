import os

from google import genai
from google.genai import types

from agent.models import TestCaseResponse
from agent.env import ENV_PATH, ensure_env_loaded
from agent.json_utils import parse_json_response
from agent.llm_config import LLM_TEMPERATURE

DEFAULT_MODEL = "gemini-2.5-flash-lite"


def _gen_config(**kwargs) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=LLM_TEMPERATURE,
        **kwargs,
    )


def generate(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> TestCaseResponse:
    ensure_env_loaded()
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"GEMINI_API_KEY is not set. Add it to {ENV_PATH} "
            "(get a free key at https://aistudio.google.com/apikey)"
        )

    model_name = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=f"{system_prompt}\n\n{user_message}",
            config=_gen_config(
                response_mime_type="application/json",
                response_schema=TestCaseResponse,
            ),
        )
        if response.text:
            return parse_json_response(response.text)
    except Exception:
        pass

    response = client.models.generate_content(
        model=model_name,
        contents=f"{system_prompt}\n\n{user_message}\n\nRespond with JSON only.",
        config=_gen_config(response_mime_type="application/json"),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return parse_json_response(response.text)
