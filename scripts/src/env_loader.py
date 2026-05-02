"""Environment loader - loads .env from the document_polishing project root.

Used by orchestration entry points before constructing any ModelManager so that
environment variables referenced by ``api_key_env`` config fields are available.
"""

from pathlib import Path

from dotenv import load_dotenv

# Path to the document_polishing project root (parent of scripts/)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


def load_project_env() -> None:
    """Load ``document_polishing/.env`` into process environment variables.

    Existing environment variables are not overridden (``override=False``).
    Missing ``.env`` files are silently ignored — the file is optional.
    """
    if _ENV_FILE.exists():
        load_dotenv(dotenv_path=_ENV_FILE, override=False)
