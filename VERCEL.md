# Vercel deployment

Use Python 3.12, the pinned requirements, and `api/wsgi.py` as the WSGI entry point. `vercel.json` collects static assets and routes requests to Django.

Configure every production variable documented in README.md **before building**. Production requires PostgreSQL, SMTP, a strong signing key, exact allowed hosts, a canonical HTTPS origin, and persistent S3 media storage. Debug/SQLite/local uploads are not a production fallback.

Apply database migrations in a controlled release job before serving traffic. Verify actual SMTP delivery, activation, upload persistence, and owner-only exports against a staging environment. This repository does not create a database, bucket, or hosting account automatically.
