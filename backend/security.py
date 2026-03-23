from __future__ import annotations

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
