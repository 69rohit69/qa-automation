"""Disk cache for identical AC → same test case output."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from agent.env import PROJECT_ROOT, ensure_env_loaded
from agent.models import TestCaseResponse

# Bump when prompts/schema change so cache is invalidated
PROMPT_VERSION = "3"

CACHE_DIR = PROJECT_ROOT / ".cache" / "responses"


def _cache_enabled() -> bool:
    ensure_env_loaded()
    raw = os.environ.get("RESPONSE_CACHE", "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _normalize(text: str) -> str:
    return "\n".join(line.strip() for line in text.strip().splitlines() if line.strip())


def cache_key(
    acceptance_criteria: str,
    *,
    context: str = "",
    model: str | None = None,
    provider: str | None = None,
) -> str:
    ensure_env_loaded()
    provider_name = provider or os.environ.get("PROVIDER", "gemini")
    model_name = model or os.environ.get(
        f"{provider_name.upper()}_MODEL",
        os.environ.get("GEMINI_MODEL", ""),
    )
    payload = "|".join(
        [
            PROMPT_VERSION,
            provider_name.lower(),
            model_name,
            _normalize(context),
            _normalize(acceptance_criteria),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get_cached(
    acceptance_criteria: str,
    *,
    context: str = "",
    model: str | None = None,
) -> TestCaseResponse | None:
    if not _cache_enabled():
        return None
    key = cache_key(acceptance_criteria, context=context, model=model)
    path = _path(key)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return TestCaseResponse.model_validate(data)
    except (json.JSONDecodeError, OSError, ValueError):
        return None


def save_cached(
    acceptance_criteria: str,
    response: TestCaseResponse,
    *,
    context: str = "",
    model: str | None = None,
) -> None:
    if not _cache_enabled():
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = cache_key(acceptance_criteria, context=context, model=model)
    _path(key).write_text(
        response.model_dump_json(indent=2),
        encoding="utf-8",
    )
