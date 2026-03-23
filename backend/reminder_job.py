from __future__ import annotations

from backend.database import SessionLocal
from backend.services import send_due_reminders


def main():
    db = SessionLocal()
    try:
        sent = send_due_reminders(db)
        print(f"Sent {sent} reminder(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
