import json

from agent.models import TestCaseResponse


def parse_json_response(text: str) -> TestCaseResponse:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    data = json.loads(text)
    return TestCaseResponse.model_validate(data)
