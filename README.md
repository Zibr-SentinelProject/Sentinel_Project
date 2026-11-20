# Sentinel_Project
#### (CC) Proyect developed by Wara, Yaxche & Dani

Sentinel is a small Flask app to report and follow security incidents. Employees open incidents, analysts handle them and admins manage the users.

- **Phase 1:** the first version of the app (incidents, comments, attachments).
- **Phase 2:** attack surface, authentication and access control (see [Phase 2: security](#phase-2-security)).

## Models

Plain Python classes in `app/models/`. They hold data and simple rules, no database code.

| Model | What it is |
|-------|------------|
| `User` | Base user (`name`, `email`, `password`). Subclasses: `Employee`, `Analyst` and `Admin`. Each role is a class that answers yes/no questions called capabilities (`view_all_incidents()`, `handle_incidents()`, `admin_all_users()`). `ROLE_CLASSES` maps the `role` column of the database to its class. |
| `Incident` | A reported incident: title, description, severity (LOW/MEDIUM/HIGH/CRITICAL), state (OPEN/PENDING/CLOSED), dates, reporter and assigned analyst. |
| `Comment` | A message written by a user on an incident. |
| `Attachment` | A file uploaded to an incident. |

The tables live in `init.sql`.

## Layers

A request goes top to bottom. Each layer only talks to the one below it.

```
Browser -> routes -> services -> repositories -> database (MariaDB)
           app/routes  app/services  app/repositories  app/db
```

- **routes** (`app/routes/`): Flask blueprints. Read the request, call a service, render a template from `app/templates/`.
- **services** (`app/services/`): business rules (e.g. who can see which incident). `factory.py` is the only file that connects services to the database.
- **repositories** (`app/repositories/`): all the SQL (parameterized queries). Return model objects.
- **models** (`app/models/`): the data classes above.

## Repository contents

### Application (`app/`)

| Folder | What's inside |
|--------|---------------|
| `db/` | Database connection (`database.py`). |
| `models/` | `User` (with `Employee`, `Analyst` and `Admin`), `Incident`, `Comment` and `Attachment`. |
| `repositories/` | All the SQL. `abc_repo.py` is the abstract base class every repository extends. |
| `services/` | Business rules. `authorization.py` decides who can do what. `factory.py` wires services to repositories, and `link_service.py` fetches the page title of an incident's source link. |
| `routes/` | Flask blueprints, one per area (see below). |
| `templates/` | Jinja2 pages. `base.html` is the shared layout. |
| `utils/` | `security.py`: password hashing and checking with bcrypt. |
| `static/` | Stylesheet (`css/style.css`) and favicon (`img/favicon.svg`). |

### Routes (`app/routes/`)

| File | Handles |
|------|---------|
| `common.py` | Home page, `current_user()`, the `requires_permission(action)` decorator and the error handlers. |
| `auth.py` | Register, log in, log out (POST) and change password. |
| `incidents.py` | List, create, view, assign and close incidents. |
| `comments.py` | Comments on an incident. |
| `attachments.py` | Download an incident's attachment. |
| `users.py` | List users and change roles (admins only). The routes to create users (`/users/new`) are commented out (see below). |

### Tests and docs

| Path | What's inside |
|------|---------------|
| `tests/unit/` | Tests for models, repositories, services and the authorization rules. |
| `tests/functional/` | Tests of the whole app through the Flask test client: login and sessions, access to other users' incidents and routes (`test_access_other_routes.py`), roles over HTTP, user management and error redirects. |
| `docs/Sentinel-Project-Report.md` | Phase 1 security and design report. |

### Project files (root)

| File | Purpose |
|------|---------|
| `run.py` | Entry point. Exposes the `app` variable that Flask looks for. |
| `init.sql` | Creates the tables, the initial admin and the initial analyst. |
| `Dockerfile` | Image for the web app. |
| `docker-compose.yml` | Web app + MariaDB for development. |
| `env.example` | Template for your `.env` (database, secret key and cookie settings). |
| `requirements.txt` | Python dependencies. |
| `pyproject.toml` | `ruff` and `pytest` configuration. |
| `.github/workflows/ci.yml` | CI that runs on every push and pull request. |

## Phase 2: security

Phase 2 fixed the incident INC-2026-001 (an IDOR: changing the ID in the URL showed the incident of another user) and its root cause: the app loaded an object without checking if the user could see it.

### Authentication

- **Passwords:** stored as salted bcrypt hashes (`app/utils/security.py`), never in plain text. Length: 8 characters minimum, 72 bytes maximum (a limit of bcrypt).
- **Login:** the same error message for a wrong email or a wrong password. A dummy hash is checked when the email does not exist, so the response time does not show which emails are registered.
- **Session:** Flask signed cookie (`session`) with only `user_id` and `user_name`. The role is never stored in it: `current_user()` loads the user and the role from the database on every request.

| Setting | Value |
|---------|-------|
| `SECRET_KEY` | Read from the environment (`.env`). Use a long random value. |
| `SESSION_COOKIE_HTTPONLY` | `True` |
| `SESSION_COOKIE_SAMESITE` | `Lax` |
| `SESSION_COOKIE_SECURE` | From the `SESSION_COOKIE_SECURE` variable (`false` by default, for local HTTP). Set it to `true` when the app is served over HTTPS. |
| `PERMANENT_SESSION_LIFETIME` | 2 hours, renewed on every request (`SESSION_REFRESH_EACH_REQUEST`), so it is an inactivity timeout. |

- `session.clear()` runs at login, register and logout (no session fixation). `session.permanent = True` is set at login and register so the 2 hours apply.
- Logout is a `POST` route, so another site cannot log the user out with a link or an image.

### Authorization

Three roles. Every account created in `/register` is an `Employee`; only an `Admin` can change a role (and nobody can change their own).

| Role | Can do |
|------|--------|
| Employee | Report incidents. See, comment on and download the attachments of their own incidents. |
| Analyst | See all incidents. Take free incidents, comment on and close the ones assigned to them. |
| Admin | Manage users (list, change roles). Read every incident. Cannot handle incidents. |

One mechanism decides everything, in `app/services/authorization.py`:

- `authorize(user, action, incident=None) -> bool` is the only code that reads the role capabilities and compares the creator or the assigned analyst of an incident. It denies by default.
- `require(user, action, incident=None)` calls `authorize` and raises `AccessDeniedError` if the answer is no: **404** when the action is about an incident (the app does not confirm it exists), **403** when there is only a role (managing users).
- `IncidentService.get_incident(user, id, action)` loads an incident and checks the permission in the same step. Every operation on an incident (view, comment, download, assign, close) uses it.
- Routes that do not depend on a specific object (`/users`...) use the `@requires_permission(action)` decorator.
- Nothing from the browser is trusted: IDs, roles and hidden fields are checked on the server (for example, the analyst of an assignment must be allowed to receive incidents).

### Pending and decisions

- **Creating users from the admin panel is disabled.** The routes `GET` and `POST /users/new` in `app/routes/users.py` are commented out, and nothing links to the page `new_user.html`. Anyone can already register freely (`/register`) and an admin can change roles (`POST /users/<id>/role`), so keeping the route would make the attack surface bigger without any benefit. `UserService.create_user()` is kept, and the group still has to comment it out while the free registration is available. If registration is closed, enable the routes again and add a link in `users.html`.
- **Deleting users is not implemented**, to avoid orphan tickets: incidents point to the user who created them and to the analyst assigned to them, and they would be left without an owner.

### Known risks (not fixed in this phase)

Documented in the Phase 2 report, section 7: no CSRF tokens, stored XSS in comments (`|safe`), uploaded files without type or size limits, no HTTPS and Secure cookie by default, server requests to user URLs (SSRF), unhandled server error pages, no login rate limit, no security headers and open registration.

## Run in development (Docker)

Needs Docker with Compose.

```bash
docker compose up --build
```

Open http://localhost:5000 and log in with one of the initial accounts (change the passwords after the first login):

| Role | Email | Password |
|------|-------|----------|
| Admin (manages users) | `admin@sentinel.local` | `admin123` |
| Analyst (handles incidents) | `analyst@sentinel.local` | `analyst123` |

> **Port 5000 already in use?** If you get `ports are not available: ... 0.0.0.0:5000: bind: address already in use`, another program is using port 5000 on your machine. On macOS this is usually **AirPlay Receiver** (System Settings → General → AirDrop & Handoff → turn off "AirPlay Receiver"). It can also happen on Windows or Linux with any other app on that port. To fix it, either free the port or change the host port in `docker-compose.yml` (for example `"8080:5000"`) and open http://localhost:8080 instead.

The code folder is mounted into the container, so edits reload automatically. The database is created from `init.sql` the first time only. To reset it:

```bash
docker compose down -v
```

`docker-compose.yml` uses a fixed `SECRET_KEY` and `FLASK_DEBUG` only for development. Do not use these values in production.

## Run without Docker

You need Python 3.12 and a MariaDB/MySQL server.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp env.example .env        # then edit it with your database data and a long random SECRET_KEY
mysql -u <user> -p <db_name> < init.sql
flask --app run run --debug
```

## Tests and lint

```bash
pytest
ruff check .
```

---
Made by Potato Team - Dani, Yaxche and Wara
