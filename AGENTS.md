# AGENTS.md

Django 6.1 + Python 3.13 marketing site for JJ Construmadera SAS (Colombia). Spanish-only UI, models, templates, and commit messages — keep new strings in Spanish (`es-co`, `America/Bogota`).

## Commands (Windows venv, run from WSL as `python.exe`)

- Tests: `.venv/Scripts/python.exe manage.py test core` (Django TestCase in `core/tests.py`; no pytest/lint/CI configured)
- Migrate: `.venv/Scripts/python.exe manage.py migrate` (use `makemigrations core` for model changes; migrations are committed)
- Server: `python manage.py runserver`

## Environment

- `settings.py` loads `.env` via `python-dotenv`. `.env` is gitignored and already present locally; mirror new vars into `.env.example`.
- DB toggle: `USE_SQLITE=True` → SQLite; `False` → PostgreSQL (uses `DB_*` vars). Analytics/leads live in whichever DB is active.

## Architecture

- Single app `core`. Templates live repo-level in `templates/` (owner-panel pages are `owner_*.html`).
- **Two admin surfaces, do not mix them:**
  - Django admin at `/admin/` (`core/admin.py`).
  - Custom owner CMS at `/owner/*` (`core/urls.py`), protected by `@login_required(login_url='owner_login')` + `@staff_member_required`. This is the primary editing UI; tests assert owner templates never link to `/admin/`.
- Content editing uses `SiteContent` rows keyed by slugs defined in `SECTION_EDITOR_MAP` (`core/views.py`) — e.g. `home_hero_title`, `about_description`. Rows are `get_or_create`'d on demand; view functions hold the fallback defaults.
- Portfolio has a **dual category system**: newer `PortfolioCategory` (slug-based) plus the legacy `PortfolioProject.category` CharField with hardcoded choices. `get_portfolio_category_items()` (views) and `get_portfolio_category_choices()` (forms) merge both — keep them in sync when touching categories.
- `PortfolioImage.save()` (`core/models.py`) auto-generates optimized (≤1600px) and thumb (800×600) versions with Pillow and **silently swallows all exceptions** — image uploads "succeed" even if processing fails. Changing this affects every image upload.
- Contact form creates a `Lead`, then redirects to a `wa.me` WhatsApp URL (`WHATSAPP_BUSINESS_NUMBER`). Tests assert this redirect and the 5-minute duplicate-submission guard in `contact` (views).
- `AnalyticsMiddleware` records a `PageVisit` on every GET except `/admin/`, `/static/`, `/media/`, and `/favicon.ico` — visible in `/owner/analytics/`.

## Gotchas

- `.venv` is a Windows venv (`Scripts/`, `python.exe`); do not recreate it or run plain `python`.
- `staticfiles/` (STATIC_ROOT), `media/`, `db.sqlite3`, and `.env` are all gitignored build/dev artifacts — don't commit them.