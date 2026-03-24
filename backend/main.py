from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from backend.config import settings
from backend.database import Base, engine, get_db
from backend.models import User
from backend.schemas import DailyProgressResponse, ProgressIn, ReminderPreferenceIn, UserResponse
from backend.security import create_access_token, decode_access_token
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
        )
        db.add(user)
    else:
        user.google_sub = google_sub
        user.email = email
        user.display_name = display_name
        user.avatar_url = avatar_url

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
