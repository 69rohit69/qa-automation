from agent.cache import get_cached, save_cached
from agent.models import TestCaseResponse
from agent.order import enforce_response_order
from agent.providers.base import generate_with_provider

__all__ = ["generate_test_cases"]


def generate_test_cases(
    acceptance_criteria: str,
    *,
    context: str = "",
    model: str | None = None,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> tuple[TestCaseResponse, bool]:
    """
    Generate test cases from AC.

    Returns (response, from_cache).
    Same AC + context + model → same output when cache hit (unless force_refresh).
    """
    if use_cache and not force_refresh:
        cached = get_cached(acceptance_criteria, context=context, model=model)
        if cached is not None:
            return enforce_response_order(cached), True

    response = generate_with_provider(
        acceptance_criteria,
        context=context,
        model=model,
    )
    response = enforce_response_order(response)
    save_cached(acceptance_criteria, response, context=context, model=model)
    return response, False
