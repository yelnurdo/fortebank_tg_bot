"""Configuration models and loader utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class AppConfig:
    """Centralised application configuration."""

    telegram_bot_token: str
    openai_api_key: str
    gemini_api_key: str
    postgres_dsn: str
    gpt_model: str = "gpt-4.1-mini"
    gemini_model: str = "gemini-2.5-flash"
    digest_dispatch_time: time = time(hour=9, minute=0)  # 09:00 Astana time


def load_config() -> AppConfig:
    """Build the application configuration from environment variables."""

    return AppConfig(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        postgres_dsn=os.getenv(
            "POSTGRES_DSN",
            "postgresql://user:pass@localhost:5432/forte",
        ),
        gpt_model=os.getenv("GPT_MODEL", "gpt-4.1-mini"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
    )
