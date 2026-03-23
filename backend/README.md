## Backend streaks

Ce backend est optionnel. Si tu ne le lances pas, `app.py` continue de fonctionner sans auth ni streaks.

### Fonctionnalités

- connexion Google OAuth
- stockage SQLite des utilisateurs
- suivi du nombre de questions répondues par jour
- streak si l'utilisateur atteint `50` questions dans la journée
- rappel email quotidien si le quota n'est pas atteint

### Lancer en local

1. Copier `.env.example` vers `.env` et remplir :
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `SESSION_SECRET`
   - `TOKEN_SECRET`
   - variables SMTP
2. Lancer :

```bash
uvicorn backend.main:app --reload --port 8000
```

3. Configurer dans Streamlit :
   - `backend.url = "http://localhost:8000"`
   - `backend.streamlit_app_url = "http://localhost:8501"`

### Rappel email

Tu peux déclencher les rappels :

```bash
python -m backend.reminder_job
```

En production, il faut le planifier avec un cron quotidien.
