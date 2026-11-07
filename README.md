# Sentinel_Project
#### (CC) Proyect developed by Wara, Yaxche & Dani

Sentinel is a small Flask app to report and follow security incidents. Employees open incidents, analysts handle them.

## Models

Plain Python classes in `app/models/`. They hold data and simple rules, no database code.

| Model | What it is |
|-------|------------|
| `User` | Base user (`name`, `email`, `password`). Subclasses: `Employee` (reports incidents) and `Analyst` (manages incidents and users). |
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
- **repositories** (`app/repositories/`): all the SQL. Return model objects.
- **models** (`app/models/`): the data classes above.

## Repository contents

### Application (`app/`)

| Folder | What's inside |
|--------|---------------|
| `db/` | Database connection (`database.py`). |
| `models/` | `User`, `Incident`, `Comment` and `Attachment`. |
| `repositories/` | All the SQL. `abc_repo.py` is the abstract base class every repository extends. |
| `services/` | Business rules. `factory.py` wires services to repositories, and `link_service.py` fetches the page title of an incident's source link. |
| `routes/` | Flask blueprints, one per area (see below). |
| `templates/` | Jinja2 pages. `base.html` is the shared layout. |
| `static/` | Stylesheet (`css/style.css`) and favicon (`img/favicon.svg`). |

### Routes (`app/routes/`)

| File | Handles |
|------|---------|
| `common.py` | Home page. |
| `auth.py` | Register, log in, log out and change password. |
| `incidents.py` | List, create, view, assign and close incidents. |
| `comments.py` | Comments on an incident. |
| `attachments.py` | Download an incident's attachment. |
| `users.py` | Create users and change roles (analysts only). |

### Tests and docs

| Path | What's inside |
|------|---------------|
| `tests/unit/` | Tests for models, repositories and services. |
| `tests/functional/` | Tests of the whole app through the Flask test client. |
| `docs/Sentinel-Project-Report.md` | Phase 1 security and design report. |

### Project files (root)

| File | Purpose |
|------|---------|
| `run.py` | Entry point. Exposes the `app` variable that Flask looks for. |
| `init.sql` | Creates the tables and the initial analyst. |
| `Dockerfile` | Image for the web app. |
| `docker-compose.yml` | Web app + MariaDB for development. |
| `env.example` | Template for your `.env` (database and secret key). |
| `requirements.txt` | Python dependencies. |
| `pyproject.toml` | `ruff` and `pytest` configuration. |
| `.github/workflows/ci.yml` | CI that runs on every push and pull request. |

## Run in development (Docker)

Needs Docker with Compose.

```bash
docker compose up --build
```

Open http://localhost:5000 and log in with the initial analyst:

- email: `analyst@sentinel.local`
- password: `analyst123`

> **Port 5000 already in use?** If you get `ports are not available: ... 0.0.0.0:5000: bind: address already in use`, another program is using port 5000 on your machine. On macOS this is usually **AirPlay Receiver** (System Settings → General → AirDrop & Handoff → turn off "AirPlay Receiver"). It can also happen on Windows or Linux with any other app on that port. To fix it, either free the port or change the host port in `docker-compose.yml` (for example `"8080:5000"`) and open http://localhost:8080 instead.

The code folder is mounted into the container, so edits reload automatically. The database is created from `init.sql` the first time only. To reset it:

```bash
docker compose down -v
```

## Run without Docker

You need Python 3.12 and a MariaDB/MySQL server.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp env.example .env        # then edit it with your database data
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
