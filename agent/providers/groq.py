import json
import os

from openai import OpenAI

from agent.models import TestCaseResponse
from agent.json_utils import parse_json_response
from agent.llm_config import LLM_TEMPERATURE

DEFAULT_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def generate(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> TestCaseResponse:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
        )

    model_name = model or os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    schema_hint = json.dumps(TestCaseResponse.model_json_schema(), indent=2)
    user_with_schema = (
        f"{user_message}\n\n"
        f"Return JSON only matching this schema:\n{schema_hint}"
    )

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_with_schema},
        ],
        response_format={"type": "json_object"},
        temperature=LLM_TEMPERATURE,
    )

    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty response.")
    return parse_json_response(content)
