from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
import jwt
from jwt import PyJWKClient
import requests
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from backend.config import settings
from backend.database import Base, engine, get_db
from backend.models import User
from backend.schemas import AuthRequest, AuthResponse, ClerkExchangeRequest, DailyProgressResponse, ProgressIn, RegisterRequest, ReminderPreferenceIn, UserResponse
from backend.security import create_access_token, decode_access_token, hash_password, verify_password
from backend.services import build_user_response, compute_streak, send_due_reminders, update_daily_progress


oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    client_kwargs={"scope": "openid email profile"},
)

app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    ensure_legacy_columns()


def ensure_legacy_columns():
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("users")}

    with engine.begin() as connection:
        if "password_hash" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(512)"))
        if "auth_provider" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(32) DEFAULT 'google'"))
        if "clerk_user_id" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN clerk_user_id VARCHAR(255)"))


def derive_clerk_frontend_api_url() -> str:
    if settings.clerk_frontend_api_url:
        return settings.clerk_frontend_api_url.rstrip("/")

    key = settings.clerk_publishable_key
    if not key or "_" not in key:
        return ""

    encoded_part = key.split("_", 2)[-1].split("$", 1)[0]
    padding = "=" * (-len(encoded_part) % 4)
    try:
        import base64

        decoded = base64.urlsafe_b64decode(f"{encoded_part}{padding}").decode("utf-8")
    except Exception:
        return ""

    if decoded.startswith("http://") or decoded.startswith("https://"):
        return decoded.rstrip("/")
    return f"https://{decoded}".rstrip("/")


def get_clerk_jwks_url() -> str:
    if settings.clerk_jwks_url:
        return settings.clerk_jwks_url

    frontend_api_url = derive_clerk_frontend_api_url()
    if not frontend_api_url:
        raise HTTPException(status_code=500, detail="Clerk frontend API URL is not configured")
    return f"{frontend_api_url}/.well-known/jwks.json"


def verify_clerk_session_token(clerk_token: str) -> dict:
    jwks_client = PyJWKClient(get_clerk_jwks_url())
    signing_key = jwks_client.get_signing_key_from_jwt(clerk_token)
    return jwt.decode(
        clerk_token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_signature": True, "verify_exp": True, "verify_nbf": True, "verify_aud": False},
    )


def fetch_clerk_user(clerk_user_id: str) -> dict:
    if not settings.clerk_secret_key:
        raise HTTPException(status_code=500, detail="Clerk secret key is not configured")

    response = requests.get(
        f"https://api.clerk.com/v1/users/{clerk_user_id}",
        headers={"Authorization": f"Bearer {settings.clerk_secret_key}"},
        timeout=10,
    )
    if not response.ok:
        raise HTTPException(status_code=401, detail="Unable to fetch Clerk user")
    return response.json()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = auth_header.split(" ", 1)[1].strip()
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user


def normalize_streamlit_url(raw_url: str | None) -> str:
    url = (raw_url or settings.streamlit_app_url).strip()
    if not url:
        raise HTTPException(status_code=500, detail="STREAMLIT_APP_URL is not configured")
    if "://" not in url:
        url = f"https://{url}"
    return url.rstrip("/")


def append_query_params(url: str, **params: str) -> str:
    split_url = urlsplit(url)
    query = dict(parse_qsl(split_url.query, keep_blank_values=True))
    query.update(params)
    return urlunsplit(
        (
            split_url.scheme,
            split_url.netloc,
            split_url.path,
            urlencode(query),
            split_url.fragment,
        )
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/auth/google/login")
async def auth_google_login(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    redirect_uri = request.url_for("auth_google_callback")
    next_param = request.query_params.get("next")
    next_url = normalize_streamlit_url(next_param or settings.streamlit_app_url)

    request.session["auth_next_url"] = next_url
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth.google.userinfo(token=token)

    email = user_info["email"].strip().lower()
    google_sub = user_info["sub"]
    display_name = user_info.get("name") or email.split("@", 1)[0]
    avatar_url = user_info.get("picture")

    user = db.scalar(select(User).where(User.google_sub == google_sub))
    if user is None:
        user = db.scalar(select(User).where(User.email == email))

    if user is None:
        user = User(
            google_sub=google_sub,
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            auth_provider="google",
        )
        db.add(user)
    else:
        user.google_sub = google_sub
        user.email = email
        user.display_name = display_name
        user.avatar_url = avatar_url
        user.auth_provider = "google"

    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)
    next_url = normalize_streamlit_url(request.session.pop("auth_next_url", settings.streamlit_app_url))
    redirect_url = append_query_params(next_url, auth_token=access_token)
    html = f"""
    <!doctype html>
    <html lang="fr">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Connexion Google</title>
      </head>
      <body style="font-family: sans-serif; padding: 24px;">
        <p>Connexion réussie. Redirection vers l'application...</p>
        <p><a href="{redirect_url}">Continuer</a></p>
        <script>
          window.location.replace({redirect_url!r});
        </script>
      </body>
    </html>
    """
    return HTMLResponse(html)


@app.post("/auth/register", response_model=AuthResponse)
def register_with_password(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="Un compte existe déjà pour cet email")

    display_name = (payload.display_name or email.split("@", 1)[0]).strip()
    user = User(
        google_sub=f"local:{email}",
        email=email,
        display_name=display_name,
        password_hash=hash_password(payload.password),
        auth_provider="password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)
    return AuthResponse(access_token=access_token, user=build_user_response(db, user))


@app.post("/auth/login", response_model=AuthResponse)
def login_with_password(payload: AuthRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")

    access_token = create_access_token(user.id)
    return AuthResponse(access_token=access_token, user=build_user_response(db, user))


@app.post("/auth/clerk/exchange", response_model=AuthResponse)
def exchange_clerk_token(payload: ClerkExchangeRequest, db: Session = Depends(get_db)):
    claims = verify_clerk_session_token(payload.clerk_token)
    clerk_user_id = claims.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Invalid Clerk token")

    clerk_user = fetch_clerk_user(clerk_user_id)
    email_addresses = clerk_user.get("email_addresses", [])
    primary_email_id = clerk_user.get("primary_email_address_id")
    primary_email = next(
        (
            item.get("email_address")
            for item in email_addresses
            if item.get("id") == primary_email_id
        ),
        None,
    ) or next((item.get("email_address") for item in email_addresses if item.get("email_address")), None)

    if not primary_email:
        raise HTTPException(status_code=400, detail="Clerk user has no email address")

    first_name = (clerk_user.get("first_name") or "").strip()
    last_name = (clerk_user.get("last_name") or "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part).strip()
    display_name = full_name or primary_email.split("@", 1)[0]
    avatar_url = clerk_user.get("image_url")

    user = db.scalar(select(User).where(User.clerk_user_id == clerk_user_id))
    if user is None:
        user = db.scalar(select(User).where(User.email == primary_email.lower()))

    if user is None:
        user = User(
            google_sub=f"clerk:{clerk_user_id}",
            clerk_user_id=clerk_user_id,
            email=primary_email.lower(),
            display_name=display_name,
            avatar_url=avatar_url,
            auth_provider="clerk",
        )
        db.add(user)
    else:
        user.clerk_user_id = clerk_user_id
        user.google_sub = f"clerk:{clerk_user_id}"
        user.email = primary_email.lower()
        user.display_name = display_name
        user.avatar_url = avatar_url
        user.auth_provider = "clerk"

    db.commit()
    db.refresh(user)

    access_token = create_access_token(user.id)
    return AuthResponse(access_token=access_token, user=build_user_response(db, user))


@app.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_user_response(db, user)


@app.post("/progress", response_model=DailyProgressResponse)
def post_progress(payload: ProgressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    progress = update_daily_progress(
        db=db,
        user=user,
        answered_questions=payload.answered_questions,
        correct_answers=payload.correct_answers,
    )
    return DailyProgressResponse(
        day=progress.day,
        answered_questions=progress.answered_questions,
        correct_answers=progress.correct_answers,
        quizzes_completed=progress.quizzes_completed,
        goal_reached=progress.goal_reached,
        streak=compute_streak(db, user.id),
    )


@app.post("/preferences/reminders")
def update_reminder_preference(
    payload: ReminderPreferenceIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.reminder_opt_in = payload.reminder_opt_in
    db.add(user)
    db.commit()
    db.refresh(user)
    return build_user_response(db, user)


@app.post("/jobs/send-reminders")
def trigger_reminders(admin_secret: str, db: Session = Depends(get_db)):
    if admin_secret != settings.token_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"sent": send_due_reminders(db)}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})
