from pathlib import Path

from dotenv import load_dotenv

# Project root: parent of agent/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
_loaded = False


def ensure_env_loaded() -> None:
    """Load .env from project root (cwd may differ when using Streamlit)."""
    global _loaded
    if not _loaded:
        load_dotenv(ENV_PATH, override=True)
        _loaded = True
