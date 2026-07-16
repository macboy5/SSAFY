import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
FRONTEND_ENV_PATH = REPO_ROOT / "frontend" / ".env"

PROCESS_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
PROCESS_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "")
PROCESS_SEOUL_CITYDATA_API_KEY = os.environ.get("SEOUL_CITYDATA_API_KEY", "")
PROCESS_SEOUL_POPULATION_API_KEY = os.environ.get("SEOUL_POPULATION_API_KEY", "")
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR", str(REPO_ROOT / "data")))


def get_openai_settings() -> tuple[str, str]:
    """Re-read .env so a newly added API key works on the next request."""
    file_values = dotenv_values(BACKEND_DIR / ".env")
    # Compatibility for the current local setup: variables without a VITE_
    # prefix are not exposed to the browser bundle. New setups should keep the
    # secret in backend/.env, but an existing frontend/.env key still works.
    legacy_values = dotenv_values(FRONTEND_ENV_PATH)
    key = (
        PROCESS_OPENAI_API_KEY
        or str(file_values.get("OPENAI_API_KEY") or "")
        or str(legacy_values.get("OPENAI_API_KEY") or "")
    )
    model = (
        PROCESS_OPENAI_MODEL
        or str(file_values.get("OPENAI_MODEL") or "")
        or str(legacy_values.get("OPENAI_MODEL") or "")
        or "gpt-5-mini"
    )
    return key.strip(), model.strip()


def get_seoul_citydata_api_key() -> str:
    """Keep the Seoul Open Data key server-side and pick up .env changes live."""
    file_values = dotenv_values(BACKEND_DIR / ".env")
    key = PROCESS_SEOUL_CITYDATA_API_KEY or str(
        file_values.get("SEOUL_CITYDATA_API_KEY") or ""
    )
    return key.strip()


def get_seoul_population_api_key() -> str:
    """Separate key issued for the 실시간 유동인구(citydata_cmrcl) dataset.

    Falls back to the general citydata key when unset, since Seoul Open Data
    Plaza often approves one account-wide key across the whole 실시간
    도시데이터 family of endpoints.
    """
    file_values = dotenv_values(BACKEND_DIR / ".env")
    key = PROCESS_SEOUL_POPULATION_API_KEY or str(
        file_values.get("SEOUL_POPULATION_API_KEY") or ""
    )
    return key.strip() or get_seoul_citydata_api_key()
