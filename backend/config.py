from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "O Mestre do Portugues Backend")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./backend/streaks.db")
    streamlit_app_url: str = os.getenv("STREAMLIT_APP_URL", "http://localhost:8501")
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    session_secret: str = os.getenv("SESSION_SECRET", "change-me")
    token_secret: str = os.getenv("TOKEN_SECRET", "change-me-too")
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_sender: str = os.getenv("SMTP_SENDER", "")
    smtp_use_tls: bool = _bool_env("SMTP_USE_TLS", True)
    daily_goal: int = int(os.getenv("DAILY_GOAL", "50"))
    reminder_subject: str = os.getenv("REMINDER_SUBJECT", "Ton streak portugais t'attend")
    reminder_enabled: bool = _bool_env("REMINDER_ENABLED", True)


settings = Settings()
