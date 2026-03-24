from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import tomllib

from dotenv import load_dotenv


load_dotenv()
load_dotenv("backend/.env")


SECRETS_PATH = Path(".streamlit/secrets.toml")


def _load_toml_secrets():
    if not SECRETS_PATH.exists():
        return {}
    with SECRETS_PATH.open("rb") as f:
        return tomllib.load(f)


_TOML_SECRETS = _load_toml_secrets()


def _nested_get(data, *keys, default=""):
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_setting(env_name: str, *secret_keys, default=""):
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value
    secret_value = _nested_get(_TOML_SECRETS, *secret_keys, default=default)
    return secret_value if secret_value not in (None, "") else default


def _get_bool_setting(env_name: str, *secret_keys, default: bool = False) -> bool:
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value.strip().lower() in {"1", "true", "yes", "on"}

    secret_value = _nested_get(_TOML_SECRETS, *secret_keys, default=None)
    if isinstance(secret_value, bool):
        return secret_value
    if isinstance(secret_value, str) and secret_value:
        return secret_value.strip().lower() in {"1", "true", "yes", "on"}
    return default


@dataclass(frozen=True)
class Settings:
    app_name: str = _get_setting("APP_NAME", "backend", "app_name", default="O Mestre do Portugues Backend")
    database_url: str = _get_setting("DATABASE_URL", "backend", "database_url", default="sqlite:///./backend/streaks.db")
    streamlit_app_url: str = _get_setting("STREAMLIT_APP_URL", "backend", "streamlit_app_url", default="http://localhost:8501")
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
