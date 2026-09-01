# Hotel Management API

A Django REST Framework API for managing hotel bookings — cities, buildings, rooms, reservations, and an in-stay product/order system for guests.

## Features

- **Cities, buildings, rooms** — full CRUD via ViewSets, with search, ordering, and filtering (django-filter)
- **Reservations** — check-in/check-out via a dedicated `set-status` action that stamps `check_in_date`/`check_out_date`, requires authentication
- **Products & orders** — in-stay purchases, with a computed order total and an aggregate `products/info/` endpoint
- **Auth** — registration, email activation, and password reset via [Djoser](https://djoser.readthedocs.io/), JWT access/refresh tokens via `djangorestframework-simplejwt`
- **Daily activation reminders** — a Celery Beat job emails anyone who registered but hasn't activated yet
- **Caching** — Redis-backed response caching on `cities`/`buildings` list & detail views, invalidated on write via signals
- **Rate limiting** — a 5/min burst throttle on top of the default anon/user daily limits
- **API docs** — OpenAPI schema via drf-spectacular (Swagger UI + Redoc)
- **Request profiling** — django-silk, mounted at `/silk/`

## Tech stack

Django 5.2 · Django REST Framework · Djoser · SimpleJWT · django-filter · drf-spectacular · Celery · Redis (cache broker + result backend) · django-environ · SQLite (default; swappable via `DATABASE_URL`)

## Setup

Requires Python 3.10+ and a running Redis server.

1. **Clone and create a virtualenv**

   ```bash
   git clone git@github.com:Sultan-Badmus/Hotel-Management.git
   cd Hotel-Management
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Redis** — needed for caching, throttling, and Celery. Install and run it locally (e.g. `brew install redis && brew services start redis` on macOS), or point `REDIS_URL` at an existing instance.

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Then fill in `.env` — see the [Environment variables](#environment-variables) table below. At minimum, set `SECRET_KEY` to something random.

4. **Migrate and run**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

   The API is now at `http://localhost:8000/`.

5. **Celery worker + beat** (only needed for the daily activation-reminder email; skip if you don't need it running)

   ```bash
   celery -A django_projects worker -B -l info
   ```

   In production, run the worker and beat scheduler as separate long-lived processes against the same Redis broker.

## API overview

| Path | What |
|---|---|
| `/cities/`, `/buildings/`, `/rooms/`, `/reservations/`, `/products/`, `/orders/`, `/order-items/` | Resource ViewSets (router-generated) |
| `/reservations/{id}/set-status/` | `POST {"status": "CI"}` or `{"status": "CO"}` — check a reservation in/out |
| `/products/info/` | Aggregate product count + max price |
| `/auth/users/` | Register (`POST`) |
| `/auth/users/activation/` | Activate a new account (`POST {"uid", "token"}`) |
| `/auth/users/reset_password/` | Request a password reset email |
| `/auth/users/reset_password_confirm/` | Complete a password reset |
| `/auth/users/me/` | Current user's profile |
| `/api/token/`, `/api/token/refresh/` | JWT obtain / refresh |
| `/api/schema/swagger-ui/`, `/api/schema/redoc/` | Interactive API docs |
| `/admin/` | Django admin |
| `/silk/` | Request profiling dashboard |

## Environment variables

All read from `.env` via `django-environ` — see `.env.example` for the full template.

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | *(required, no default)* |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `[]` |
| `DATABASE_URL` | Database connection string | `sqlite:///db.sqlite3` |
| `REDIS_URL` | Redis URL — cache, throttling, Celery broker/backend | `redis://127.0.0.1:6379/1` |
| `EMAIL_BACKEND` | Django email backend | console backend |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP settings (e.g. Gmail — see comment in `.env.example`) | unset |
| `DEFAULT_FROM_EMAIL` | From-address for outgoing mail | `webmaster@localhost` |
| `FRONTEND_DOMAIN`, `FRONTEND_PROTOCOL`, `FRONTEND_SITE_NAME` | Used to build activation/password-reset links in emails | `localhost:3000`, `http`, `Hotel Management` |

## Project structure

```
django_projects/       Project settings, root urls, Celery app
hotel_management/      The one app: models, serializers, views, urls,
                        permissions, pagination, throttles, filters,
                        signals (cache invalidation), tasks (Celery),
                        emails (custom Djoser email templates)
```
