## Deploying on Vercel

### 1) Prerequisites
- Push this repo to GitHub/GitLab/Bitbucket.
- Create a Vercel project from the repo.

### 2) Required Environment Variables
- `SECRET_KEY`: a long random Django secret.
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `.vercel.app,<your-custom-domain>`
- `CSRF_TRUSTED_ORIGINS`: `<your-vercel-domain>,<your-custom-domain>`
- `DATABASE_URL`: recommended (Vercel Postgres or any managed Postgres URL).

### 3) Database Note
- SQLite on Vercel is not suitable for persistent writes.
- Use Postgres in production (`DATABASE_URL`).

### 4) Deploy
- `vercel` (preview)
- `vercel --prod` (production)
