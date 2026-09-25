"""
Settings, read from environment variables (via a .env file if present) so the
same code runs locally and in any deployment environment.

Copy .env.example to .env and fill in your own values; .env is git-ignored.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.name} "
            f"user={self.user} password={self.password}"
        )


@dataclass(frozen=True)
class PipelineConfig:
    source: str  # "csv" or "api"
    csv_path: str
    api_url: str
    db: DbConfig


def _get(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value if value is not None else default


def load_config() -> PipelineConfig:
    source = _get("SOURCE", "csv").strip().lower()

    if source not in ("csv", "api"):
        raise ValueError(f"SOURCE must be 'csv' or 'api', got '{source}'")

    if source == "api" and not _get("API_URL"):
        raise ValueError("API_URL must be set when SOURCE=api")

    return PipelineConfig(
        source=source,
        csv_path=_get("CSV_PATH", "data/sample_crime_stats.csv"),
        api_url=_get("API_URL"),
        db=DbConfig(
            host=_get("DB_HOST", "localhost"),
            port=int(_get("DB_PORT", "5432")),
            name=_get("DB_NAME", "crime_data"),
            user=_get("DB_USER", "postgres"),
            password=_get("DB_PASSWORD", "postgres"),
        ),
    )
