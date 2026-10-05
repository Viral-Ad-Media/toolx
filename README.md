# Tool-X

Tool-X is a Django web app for creating structured ad copy and paraphrase drafts, with user accounts, profile management, and document export (PDF/DOCX).

## What This App Does

- User registration, login, logout, password reset, and account activation email flow.
- Create and save ad copy records using a guided 12-part structure.
- Create and save paraphrase entries.
- View your own saved entries in dashboard/history pages.
- Export ad copy entries to:
  - PDF (`reportlab`)
  - DOCX (`python-docx`)
- Basic profile management with avatar upload validation.

## Tech Stack

- Python 3.11 (recommended for this repo)
- Django 3.2.x
- SQLite for local development
- Optional PostgreSQL in production via `DATABASE_URL`
- WhiteNoise for static files
- Crispy Forms + TinyMCE + django-social-share

## Project Structure

```text
toolx/
├── api/                      # Vercel serverless entrypoint
├── instant_generator/        # Core app (models, views, forms, routes)
├── static/                   # Source static assets
├── templates/                # Base + auth + marketing templates
├── toolx/                    # Django project config (settings, urls, wsgi)
├── manage.py
├── requirements.txt
├── vercel.json
└── README.md
```

## Prerequisites

- Python 3.11+
- `pip`
- `venv` module (`python3 -m venv`)

## Local Development Setup

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

3. Create environment variables.

Create a `.env` file in the project root with values similar to:

```env
SECRET_KEY=replace-with-a-long-random-value
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=

LOGIN_URL=/login/
LOGOUT_URL=/logout/
LOGIN_REDIRECT_URL=/dashboard/
LOGOUT_REDIRECT_URL=/

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_PORT=25
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False

ADMIN_EMAIL=admin@example.com
SUPPORT_EMAIL=support@example.com

# Optional production-style DB override:
# DATABASE_URL=postgres://user:pass@host:5432/dbname
```

4. Apply migrations and run the server.

```bash
python manage.py migrate
python manage.py runserver
```

5. Open the app:

- `http://127.0.0.1:8000/`

## Configuration Notes

- If `DATABASE_URL` is not set, the app uses local SQLite (`db.sqlite3`).
- If `DATABASE_URL` is set, Django uses that database (PostgreSQL recommended for production).
- Static files are served using WhiteNoise.
- In `DEBUG=True`, media URLs are served by Django dev server.

## Key Routes

### Public

- `/` Home page
- `/features/` Features page
- `/pricing/` Pricing page
- `/signup/` Sign up
- `/login/` Login
- `/logout/` Logout
- `/password_reset/` Password reset flow
- `/activate/<uidb64>/<token>/` Account activation link

### Authenticated

- `/dashboard/` User dashboard
- `/profile/` Profile page
- `/profile/edit` Edit profile + avatar
- `/create/` Create ad copy
- `/my_adcopies/` List ad copies
- `/preview/<id>` View one ad copy (owner only)
- `/pdf/<id>` Export ad copy as PDF (owner only)
- `/docx/<id>` Export ad copy as DOCX (owner only)
- `/create_paraphrase/` Create paraphrase entry
- `/paraphrase/` List paraphrase entries
- `/paraphrase_preview/<id>` View paraphrase entry (owner only)

## Data Model Overview

### `InstantGenerator`

Stores one structured ad copy with 12 text sections and timestamps:

- `Get_Attention`
- `Identify_the_Problem_Your_Audience_Have`
- `Provide_the_Solution`
- `Present_your_Credentials`
- `Show_the_Benefits`
- `Give_Social_Proof`
- `Make_Your_Offer`
- `Give_a_Guarantee`
- `Inject_Scarcity`
- `Call_to_action`
- `Give_a_Warning`
- `Close_with_a_Reminder`

### `Paraphrase`

- `Title`
- `Article`
- timestamps

### `Profile`

- `user` (1:1 with Django user)
- `avatar`
- `email_confirmed`
- timestamps

## Profile Avatar Validation

The profile form validates uploaded avatars:

- Max dimensions: `100x100`
- Allowed types: `jpeg`, `pjpeg`, `gif`, `png`
- Max file size: `20 KB`

## Running Tests

```bash
python manage.py test
```

Current tests cover:

- Access control on preview routes (owner-only)
- Profile update flow
- Signup creates inactive users pending activation

## Deployment on Vercel

This repo is configured for Vercel with:

- `api/wsgi.py` as the Python function entrypoint
- `vercel.json` rewrite to route all traffic to Django
- `collectstatic` build command

### 1) Push to Git provider

Push this project to GitHub/GitLab/Bitbucket.

### 2) Create Vercel project

Import the repository in Vercel.

### 3) Set Vercel environment variables

Required:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=.vercel.app,<your-domain>`
- `CSRF_TRUSTED_ORIGINS=<your-vercel-domain>,<your-domain>`

Recommended:

- `DATABASE_URL` (Vercel Postgres or another managed Postgres)

Optional (email/custom behavior):

- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `ADMIN_EMAIL`
- `SUPPORT_EMAIL`

### 4) Deploy

```bash
vercel
vercel --prod
```

### Important Production Notes

- Do not rely on SQLite for production on Vercel.
- Vercel filesystem is ephemeral; user-uploaded media will not persist reliably.
- Use object storage (S3, Cloudinary, etc.) for persistent media in production.

## Common Issues

### `pg_config executable not found`

If this appears during install, you are trying to compile `psycopg2` from source.

This project uses `psycopg2-binary` in `requirements.txt`, which avoids local `pg_config` builds.

### Collectstatic failures

Make sure static directories exist and dependencies installed:

```bash
python manage.py collectstatic --noinput
```

## Security Checklist (Production)

- Set a strong `SECRET_KEY`
- Keep `DEBUG=False`
- Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` correctly
- Use PostgreSQL via `DATABASE_URL`
- Move media uploads to persistent cloud storage

