## Backend comptes, streaks et rappels

L'application Streamlit continue de marcher sans ce backend. Si le backend est coupé, seule la partie profil/streaks disparaît.

### Ce qui a été ajouté

- backend FastAPI séparé dans [`backend/main.py`](/Users/antoi/Library/Mobile Documents/com~apple~CloudDocs/Appli portugais/backend/main.py)
- auth Google OAuth
- SQLite pour les utilisateurs et la progression quotidienne
- streak journalier basé sur `50` questions répondues par jour
- rappel email via SMTP si l'objectif du jour n'est pas atteint

### Variables backend

Copier [`backend/.env.example`](/Users/antoi/Library/Mobile Documents/com~apple~CloudDocs/Appli portugais/backend/.env.example) vers `.env` et remplir :

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `SESSION_SECRET`
- `TOKEN_SECRET`
- `SMTP_HOST`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_SENDER`
- `STREAMLIT_APP_URL`

### Lancer le backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### Configurer Streamlit

Dans `secrets.toml` ou dans l'environnement :

```toml
[backend]
url = "http://localhost:8000"
streamlit_app_url = "http://localhost:8501"
```

### Déclencher les rappels

En local :

```bash
python -m backend.reminder_job
```

En production :

- planifier `python -m backend.reminder_job` une fois par jour
- ou appeler `POST /jobs/send-reminders` avec `admin_secret = TOKEN_SECRET`
