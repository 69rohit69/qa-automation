import os

from openai import OpenAI

from agent.llm_config import LLM_TEMPERATURE
from agent.models import TestCaseResponse

DEFAULT_MODEL = "gpt-4o-mini"


def generate(
    *,
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> TestCaseResponse:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    model_name = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
    client = OpenAI(api_key=api_key)

    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format=TestCaseResponse,
        temperature=LLM_TEMPERATURE,
        seed=42,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no structured test cases.")
    return parsed
