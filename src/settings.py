import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_host: str
    api_port: int
    scrape_cron: str
    scrape_timezone: str
    cors_origins: tuple[str, ...]


def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL",
            "postgresql://canaan_user:canaan_password@localhost:5435/canaan",
        ),
        api_host=os.environ.get("API_HOST", "0.0.0.0"),
        api_port=int(os.environ.get("API_PORT", "8088")),
        scrape_cron=os.environ.get("SCRAPE_CRON", "0 2 * * *"),
        scrape_timezone=os.environ.get("SCRAPE_TIMEZONE", "America/Sao_Paulo"),
        cors_origins=tuple(
            origin.strip()
            for origin in os.environ.get(
                "CORS_ORIGINS", "http://localhost:5188"
            ).split(",")
            if origin.strip()
        ),
    )
