# BuildBid — Construction Project Bidding & Management System

A Django web platform that connects **clients** (who post construction projects)
with **contractors** (who bid on them). Clients compare bids and contractor
profiles, award the project, track it to completion, and leave a review. An admin
verifies contractors and manages the platform.

Built with **Django + server-rendered Django Templates** and **Tailwind CSS**
(no React / REST API layer).

## Features

- Role-based accounts: Client, Contractor, Admin
- Contractor profiles with admin verification (license document upload)
- Project posting with category, budget range, location, deadline
- Project browsing with category / location / budget filters and pagination
- Bidding (one bid per contractor per project), bid comparison, awarding
- Two-step completion: contractor marks complete → client confirms
- Reviews & ratings (1–5) with automatic contractor rating averages
- Django admin for contractor verification and platform management

## Tech stack

- Python 3 / Django 6
- Django Templates + Tailwind CSS (compiled via the Tailwind CLI)
- SQLite (development) / MySQL (production)
- Pillow (image uploads)

## Getting started (development)

Prerequisites: Python 3.11+, Node.js (for the Tailwind build).

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install and build the Tailwind CSS
npm install
npm run build:css              # one-off build
# npm run watch:css            # rebuild on template changes (run in a 2nd terminal)

# 4. Apply database migrations (seeds project categories)
python manage.py migrate

# 5. Create an admin account (this is the platform admin)
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

Visit http://127.0.0.1:8000/. The Django admin is at `/admin/`.

> **Note on styling:** Tailwind uses a build step. If pages look unstyled, run
> `npm run build:css` (the compiled `static/css/output.css` is committed, so this
> is only needed after changing templates/classes).

## Roles & access

- **Admin access** to `/admin/` is controlled by Django's `is_staff`/`is_superuser`,
  **not** the `role` field. Create admins with `createsuperuser`. Registration only
  allows the Client and Contractor roles.
- **Contractors** must be **verified** by an admin (in `/admin/` → Contractor
  profiles → "Verify selected contractors") before they can bid.

## Running tests

```bash
python manage.py test
```

## Deployment (production)

1. Set environment variables (see `.env.example`):
   - `DJANGO_SECRET_KEY` (required), `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`
   - For MySQL: `DB_ENGINE=mysql` and `DB_*` vars, plus `pip install mysqlclient`
2. `python manage.py migrate`
3. `npm run build:css`
4. `python manage.py collectstatic`
5. Serve with a production WSGI server; configure static/media file serving.

Suitable hosts: Render, PythonAnywhere.

## Project structure

```
construction/   # project settings, root urls
accounts/       # custom User, auth, contractor profiles, verification, dashboards
projects/       # ProjectCategory, Project, posting, browsing, completion
bids/           # Bid model, bidding, awarding
reviews/        # Review model, ratings
templates/      # base layout + per-app templates
static/         # Tailwind source + compiled CSS
```
