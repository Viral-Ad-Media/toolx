# Tool-X

Tool-X stores structured sales letters and editable article drafts, with user accounts and owner-only PDF/DOCX exports. It assembles text supplied by the user. It does not offer AI generation, automated paraphrasing, subscriptions, or billing.

## Development

Use Python 3.12 and Django 5.2 LTS. `requirements.txt` pins the complete runtime dependency set; `requirements.in` declares the direct requirements.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

`.env.example` enables local debug mode and console email. Open the activation link printed to your terminal to activate a new local account. SQLite and local media storage are development-only. Neither databases nor user uploads are tracked in git. Create a local administrator using `python manage.py createsuperuser`; the repository has no seed accounts.

## Account security

Signup requires an email address. Registration emails use `PUBLIC_ORIGIN`, independent of request Host headers. Activation links expire after one hour, are invalidated by password/email/account-state changes, and can be consumed only once. Successful activation redirects to normal login; it does not create an authenticated session. A failed delivery rolls back registration so the user can retry. `/activation_resend/` responds the same way for eligible and nonexistent accounts.

`Profile.activation_pending` distinguishes registration from suspension. Existing inactive users are deliberately **not** marked pending by the migration: an administrator must verify a historical registration before marking its profile pending and sending a fresh link. Never mark a suspended account pending. Old links are invalid after the upgrade. Confirmed account email editing is disabled until a separate new-address verification workflow is implemented.

Django 5 logout uses a CSRF-protected POST. Login, signup, reset-email requests and activation resends have database-backed limits. Record creation/editing and exports are also limited across workers. Counters identify anonymous callers using `REMOTE_ADDR`; configure your trusted proxy to provide the real client address safely, rather than trusting arbitrary forwarded headers. Schedule `python manage.py prune_rate_limits` daily. Bound request sizes additionally at the ingress, especially multipart uploads.

## Content

Sales letters contain twelve manually written sections. Text sections are limited to 10,000 characters. PDF export treats submitted content as literal text, escapes markup and preserves line breaks. Both export formats refuse oversized historical records.

Article drafts retain their existing `/create_paraphrase/`, `/paraphrase/`, and `/paraphrase_preview/<id>` URLs for compatibility. The interface calls them drafts and provides an owner-only `/draft/edit/<id>/` editor. It displays the saved text once instead of pretending that a second unchanged copy is a generated result. History pages show 20 records per page; dashboard summaries show six of each type.

Avatar files must be valid supported images, at most 100×100 pixels and 20 KB. Accounts without an avatar use a bundled static fallback.

## Production deployment

Production startup intentionally fails if required configuration is missing. Configure before deploying:

- `DEBUG=False`
- `SECRET_KEY`: cryptographically random, at least 50 characters; do not reuse the old fallback
- `ALLOWED_HOSTS`: exact service/custom hostnames (no `.vercel.app` wildcard)
- `PUBLIC_ORIGIN`: your HTTPS site origin, e.g. `https://toolx.example.com`
- `DATABASE_URL`: managed PostgreSQL with TLS
- SMTP backend, host, TLS/SSL choice, port, credentials and verified sender (`ADMIN_EMAIL`)
- Private S3-compatible media bucket and region; credentials via workload identity or environment; optional endpoint override

Persistent uploads use django-storages S3 storage, private objects and signed URLs. Restrict storage credentials to the media bucket and configure the bucket yourself; naming a bucket does not provision it. SQLite/local uploads cannot silently substitute in production. HTTPS redirects, secure cookies, and HSTS for the current hostname are enabled; terminate HTTPS at a trusted proxy that strips and sets `X-Forwarded-Proto` correctly. HSTS excludes subdomains and preload.

Back up an existing database, install the locked dependencies, run `python manage.py migrate`, run `python manage.py collectstatic --noinput`, then start `gunicorn toolx.wsgi --bind 0.0.0.0:$PORT`. Run `python manage.py check --deploy --fail-level WARNING` with the actual environment. `Procfile` supports conventional hosting; `api/wsgi.py` and `vercel.json` support Vercel. Database migrations must run in a controlled release step, not on every request.

Production uploads and real SMTP delivery need end-to-end verification with your actual credentials. No ToolX service was found in the inspected Render workspace; this patch does not provision or deploy one.

## Public database incident follow-up

The earlier revision committed a populated database. This change removes it and private media from the branch, but previous commits and downloaded copies remain. Determine whether the exposed identities/passwords are used anywhere else, reset affected active credentials, invalidate relevant sessions, and rotate any exposed historical signing/email secrets. Do not use the old database to seed a new deployment. Coordinate repository-history cleanup separately; do not force-push shared history casually. Deleting a file does not revoke credentials.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
python manage.py test
python -m pip install pip-audit
pip-audit -r requirements.txt
```

GitHub Actions runs these checks plus production configuration validation. Regression tests cover activation use/replay/expiry, suspended accounts, registration delivery failures, CSRF, ownership, content limits, PDF markup, DOCX generation, draft editing, pagination, avatars, logout, and shared throttling.

To refresh dependencies in a Python 3.12 environment, install `pip-tools`, run `pip-compile --upgrade --strip-extras requirements.in`, install the resulting file, and rerun verification.
