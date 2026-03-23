from __future__ import annotations

import smtplib
from datetime import date, datetime, timedelta
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import DailyProgress, User


def get_or_create_progress(db: Session, user_id: int, day: date) -> DailyProgress:
    progress = db.scalar(select(DailyProgress).where(DailyProgress.user_id == user_id, DailyProgress.day == day))
    if progress is None:
        progress = DailyProgress(user_id=user_id, day=day)
        db.add(progress)
        db.flush()
    return progress


def update_daily_progress(
    db: Session,
    user: User,
    answered_questions: int,
    correct_answers: int,
    day: date | None = None,
) -> DailyProgress:
    target_day = day or date.today()
    progress = get_or_create_progress(db, user.id, target_day)
    progress.answered_questions += max(answered_questions, 0)
    progress.correct_answers += max(correct_answers, 0)
    progress.quizzes_completed += 1
    progress.goal_reached = progress.answered_questions >= settings.daily_goal
    progress.updated_at = datetime.utcnow()
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


def compute_streak(db: Session, user_id: int, today: date | None = None) -> int:
    current_day = today or date.today()
    streak = 0

    while True:
        progress = db.scalar(
            select(DailyProgress).where(
                DailyProgress.user_id == user_id,
                DailyProgress.day == current_day,
                DailyProgress.goal_reached.is_(True),
            )
        )
        if progress is None:
            break
        streak += 1
        current_day -= timedelta(days=1)

    return streak


def build_user_response(db: Session, user: User) -> dict:
    today_progress = db.scalar(
        select(DailyProgress).where(DailyProgress.user_id == user.id, DailyProgress.day == date.today())
    )
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "reminder_opt_in": user.reminder_opt_in,
        "streak": compute_streak(db, user.id),
        "answered_today": today_progress.answered_questions if today_progress else 0,
        "daily_goal": settings.daily_goal,
    }


def send_reminder_email(user: User, answered_today: int) -> None:
    if not settings.reminder_enabled:
        return
    if not settings.smtp_host or not settings.smtp_sender:
        return

    remaining = max(settings.daily_goal - answered_today, 0)
    message = EmailMessage()
    message["Subject"] = settings.reminder_subject
    message["From"] = settings.smtp_sender
    message["To"] = user.email
    message.set_content(
        (
            f"Salut {user.display_name},\n\n"
            f"Tu as fait {answered_today} question(s) aujourd'hui. "
            f"Il t'en reste {remaining} pour garder ton streak sur O Mestre do Portugues.\n\n"
            f"Retourne sur l'application : {settings.streamlit_app_url}\n"
        )
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


def send_due_reminders(db: Session, today: date | None = None) -> int:
    target_day = today or date.today()
    sent_count = 0
    users = db.scalars(select(User).where(User.reminder_opt_in.is_(True))).all()

    for user in users:
        progress = get_or_create_progress(db, user.id, target_day)
        already_sent = progress.reminder_sent_at is not None and progress.reminder_sent_at.date() == target_day
        if progress.goal_reached or already_sent:
            continue

        send_reminder_email(user, progress.answered_questions)
        progress.reminder_sent_at = datetime.utcnow()
        db.add(progress)
        sent_count += 1

    db.commit()
    return sent_count
