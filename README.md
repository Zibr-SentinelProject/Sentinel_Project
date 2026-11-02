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

## Run in development (Docker)

Needs Docker with Compose.

```bash
docker compose up --build
```

Open http://localhost:5000 and log in with the initial analyst:

- email: `analyst@sentinel.local`
- password: `analyst123`

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
