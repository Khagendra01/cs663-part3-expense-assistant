"""Settings for the local expense assistant.

Loads values from settings.yaml when it exists, then lets environment
variables override them. All fields have defaults, so the project runs
even before settings.yaml is created from the example file.
"""

import os
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _yaml_values() -> dict:
    for candidate in (Path.cwd() / "settings.yaml", _project_root() / "settings.yaml"):
        if candidate.is_file():
            try:
                data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            except Exception:
                return {}
            if isinstance(data, dict):
                return data
    return {}


class Settings(BaseSettings):
    """Application settings.

    Attributes:
        GCLOUD_LOCATION: Google Cloud location for Vertex AI.
        GCLOUD_PROJECT_ID: Google Cloud project id for Vertex AI.
        DB_PATH: Path to the local SQLite file, relative to the project root.
        RECEIPTS_DIR: Folder where receipt image files are kept.
        CURRENCY: Default currency for new receipts.
        BACKEND_URL: Kept for parity with the codelab starter. Not used locally.
    """

    GCLOUD_LOCATION: str = "us-central1"
    GCLOUD_PROJECT_ID: str = "cs663-dog-training"
    DB_PATH: str = "data/expenses.db"
    RECEIPTS_DIR: str = "data/receipts"
    CURRENCY: str = "USD"
    BACKEND_URL: str = "http://localhost:8081/chat"

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


def get_settings() -> Settings:
    """Return settings from settings.yaml, with env vars on top."""
    values = _yaml_values()
    for key in ("GCLOUD_LOCATION", "GCLOUD_PROJECT_ID", "DB_PATH", "RECEIPTS_DIR", "CURRENCY", "BACKEND_URL"):
        env_value = os.environ.get(key)
        if env_value:
            values[key] = env_value
    return Settings(**values)
