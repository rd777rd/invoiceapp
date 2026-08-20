# New Client Setup

This app (originally built one-off for SmallScapes) is set up to be forked and
redeployed per client. It's still single-tenant under the hood -- one deployed
instance = one client's data -- so "reselling" it today means one Render
service per client, not a shared multi-tenant platform. See the scoping notes
at the bottom for what a real multi-tenant version would require.

## 1. Fork the repo

Create a new GitHub repo (e.g. `invoiceapp-<client-slug>`) from this one. Don't
fork via GitHub's "Fork" button if you want a clean, disconnected history --
just clone this repo, remove the `origin` remote, and push to a fresh repo
instead.

## 2. Set environment variables

On the new Render service (or wherever it's deployed), set:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Generate a fresh one per deployment -- never reuse across clients. `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `COMPANY_NAME` | Recommended | Shown in the page title, invoice heading, and PDF invoice. Defaults to "Business Invoice" if unset. |
| `BREVO_API_KEY` | For email | Get one free at brevo.com. Without it, invoice emails just log instead of sending -- the app still works, invoices just won't auto-email. |
| `BREVO_SENDER_EMAIL` | For email | Must be a single-sender-verified address in Brevo (click the confirmation link Brevo emails you -- no DNS access needed). |

Copy `.env.example` to `.env` for local development with the same keys.

## 3. Deploy

Current build/start commands (Render):
- Build: `pip install -r requirements.txt`
- Start: `gunicorn invoice_project.wsgi:application`

**Known gap:** there's no `migrate` step in the build command, which means
`db.sqlite3` (committed to the repo) *is* the database -- there's no fresh-
schema bootstrap for a brand new client instance. For a new client, you'll
need to either:
- Run `python manage.py migrate` once locally against a fresh empty
  `db.sqlite3`, commit that empty-but-migrated database, and deploy from
  there, or
- Add `python manage.py migrate` to the build command and set up a real
  persistent database (SQLite on Render's free tier doesn't survive
  redeploys anyway -- see the main risk note below).

## 4. Create the first login

No signup flow is exposed publicly by default in this build's URLs (`/signup/`
exists as a view but isn't linked from anywhere) -- create the client's admin
login via `python manage.py createsuperuser` locally against the fresh
`db.sqlite3` before your first deploy, or temporarily wire up `/signup/`.

---

## Known limitations (read before reselling this to a second client)

- **Not multi-tenant.** All `Supply`/`InvoiceItem`/`Invoice` data is global --
  every logged-in user on one instance sees the same data. This is fine for
  one client per deployment, which is the current model. Do NOT put two
  clients on one instance.
- **SQLite + no persistent disk = data loss risk on every redeploy** on
  Render's free tier. This is a pre-existing risk on the live SmallScapes
  instance too, not something introduced by this cleanup. A real fix is a
  managed Postgres database (Render's free tier allows one per account) or
  a persistent disk mount.
- **This build has zero test coverage** beyond what was added alongside the
  email/branding changes in `invoices/tests.py`. Worth expanding before
  reselling this at scale.
