from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()
load_dotenv("backend/.env")


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_setting(env_name: str, *secret_keys, default=""):
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value
    return default


def _get_bool_setting(env_name: str, *secret_keys, default: bool = False) -> bool:
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value.strip().lower() in {"1", "true", "yes", "on"}
    return default


@dataclass(frozen=True)
class Settings:
    app_name: str = _get_setting("APP_NAME", "backend", "app_name", default="O Mestre do Portugues Backend")
    database_url: str = _get_setting("DATABASE_URL", "backend", "database_url", default="sqlite:///./backend/streaks.db")
    streamlit_app_url: str = _get_setting("STREAMLIT_APP_URL", "backend", "streamlit_app_url", default="http://localhost:8501")
    clerk_publishable_key: str = _get_setting("CLERK_PUBLISHABLE_KEY", "clerk", "publishable_key", default="")
    clerk_secret_key: str = _get_setting("CLERK_SECRET_KEY", "clerk", "secret_key", default="")
    clerk_frontend_api_url: str = _get_setting("CLERK_FRONTEND_API_URL", "clerk", "frontend_api_url", default="")
    clerk_jwks_url: str = _get_setting("CLERK_JWKS_URL", "clerk", "jwks_url", default="")
    google_client_id: str = _get_setting("GOOGLE_CLIENT_ID", "google_auth", "client_id", default="")
    google_client_secret: str = _get_setting("GOOGLE_CLIENT_SECRET", "google_auth", "client_secret", default="")
    session_secret: str = _get_setting("SESSION_SECRET", "backend", "session_secret", default="change-me")
    token_secret: str = _get_setting("TOKEN_SECRET", "backend", "token_secret", default="change-me-too")
    smtp_host: str = _get_setting("SMTP_HOST", "smtp", "host", default="")
    smtp_port: int = int(_get_setting("SMTP_PORT", "smtp", "port", default="587"))
    smtp_username: str = _get_setting("SMTP_USERNAME", "smtp", "username", default="")
    smtp_password: str = _get_setting("SMTP_PASSWORD", "smtp", "password", default="")
    smtp_sender: str = _get_setting("SMTP_SENDER", "smtp", "sender", default="")
    smtp_use_tls: bool = _get_bool_setting("SMTP_USE_TLS", "smtp", "use_tls", default=True)
    daily_goal: int = int(_get_setting("DAILY_GOAL", "backend", "daily_goal", default="50"))
    reminder_subject: str = _get_setting(
        "REMINDER_SUBJECT",
        "smtp",
        "reminder_subject",
        default="Ton streak portugais t'attend",
    )
    reminder_enabled: bool = _get_bool_setting("REMINDER_ENABLED", "backend", "reminder_enabled", default=True)


settings = Settings()
