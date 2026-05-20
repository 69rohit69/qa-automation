import os

from agent.env import ensure_env_loaded
from agent.models import TestCaseResponse
from agent.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

def _build_user_message(acceptance_criteria: str, context: str) -> str:
    return USER_PROMPT_TEMPLATE.format(
        context=context.strip() or "(none)",
        acceptance_criteria=acceptance_criteria.strip(),
    )


def generate_with_provider(
    acceptance_criteria: str,
    *,
    context: str = "",
    model: str | None = None,
) -> TestCaseResponse:
    ensure_env_loaded()

    ac = acceptance_criteria.strip()
    if not ac:
        raise ValueError("Acceptance criteria cannot be empty.")

    provider = os.environ.get("PROVIDER", "gemini").lower().strip()
    user_message = _build_user_message(ac, context)
    from agent.providers import gemini, groq, openai_provider

    providers = {
        "gemini": gemini.generate,
        "groq": groq.generate,
        "openai": openai_provider.generate,
    }
    if provider not in providers:
        raise RuntimeError(
            f"Unknown PROVIDER={provider!r}. Use one of: {', '.join(providers)}"
        )
    return providers[provider](
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        model=model,
    )
