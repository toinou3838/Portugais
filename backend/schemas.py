from __future__ import annotations

from datetime import date

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    avatar_url: str | None
    reminder_opt_in: bool
    streak: int
    answered_today: int
    daily_goal: int
    auth_provider: str


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(AuthRequest):
    display_name: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    user: UserResponse


class ProgressIn(BaseModel):
    answered_questions: int
    correct_answers: int = 0
    quiz_size: int | None = None


class ReminderPreferenceIn(BaseModel):
    reminder_opt_in: bool


class DailyProgressResponse(BaseModel):
    day: date
    answered_questions: int
    correct_answers: int
    quizzes_completed: int
    goal_reached: bool
    streak: int
