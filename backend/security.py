from __future__ import annotations

import hashlib
import hmac
import secrets

from itsdangerous import BadSignature, URLSafeSerializer

from backend.config import settings


serializer = URLSafeSerializer(settings.token_secret, salt="omdp-auth")


def create_access_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def decode_access_token(token: str) -> int | None:
    try:
        payload = serializer.loads(token)
    except BadSignature:
        return None

    user_id = payload.get("user_id")
    if isinstance(user_id, int):
        return user_id
    return None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 200_000
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${derived_key.hex()}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False

    try:
        algorithm, iterations_str, salt, password_hash = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations_str),
    )
    return hmac.compare_digest(derived_key.hex(), password_hash)
