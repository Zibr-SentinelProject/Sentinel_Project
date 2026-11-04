<div align="center">

# <span style="color:#1F4E79">Sentinel Report</span>

<span style="color:#2E75B6">**Security & Design Report · Project Sentinel, Phase 1**</span>

*Nexus Digital Solutions · internal incident tracker*

</div>

| | |
|---|---|
| **Programme** | Informazioaren teknologien inguruneetan zibersegurtasun |
| **Module** | EKOS |
| **Authors** | Daniel Alvarez · Yaxche Alvarez · Wara Pacheco |
| **Date** | 04/10/2026 |

---

## Index

1. [Application overview](#1-application-overview)
   - [1.1 Users](#11-users) · [1.2 Features](#12-features) · [1.3 Technology](#13-technology)
2. [Architecture](#2-architecture)
3. [Components](#3-components)
4. [Deviations from the handout](#4-deviations-from-the-handout)
5. [Shortcuts](#5-shortcuts)
6. [Preliminary security analysis](#6-preliminary-security-analysis)
   - [6.1 What we protect and who can reach it](#61-what-we-protect-and-who-can-reach-it) · [6.2 What already helps](#62-what-already-helps)

---

## 1. Application overview

Sentinel is an internal web application for Nexus Digital Solutions that replaces the shared spreadsheet, email and chat used so far to track security incidents. **Employees report incidents; analysts triage, assign, discuss and close them.**

### 1.1 Users

| Role | What they can do |
| :--- | :--- |
| **Employee** | Register, report incidents, see and comment on their own incidents, attach one file when they report an incident. |
| **Analyst** | Everything an employee can do on their own incidents, plus: see every incident, assign (claim) an incident, close the incidents assigned to them, create users with any role, list users and change roles. |

### 1.2 Features

- **Registration, login and logout.** Anyone can register, and all new accounts are created with the employee role.
- **Incident report form.** Title, description, severity, optional external link and optional file attachment.
- **Incident list.** Newest to oldest, with a title search and a severity filter.
- **Saved filter.** The selected severity filter is stored in a cookie and applied automatically the next time the list is opened.
- **Incident detail view.** Shows the incident information, comments, attachment, source link and the available management actions.
- **Comments.** Both the incident creator and the assigned analyst can add comments.
- **Attachments.** Each incident can have one optional attachment. It is uploaded when the incident is created and cannot be added later. Users who may view the incident can also download its attachment.
- **Source link.** The server fetches the external page and stores its HTML `<title>` to display it with the incident.
- **User management (analysts only).** Analysts can create users and change their roles.
- **Extras beyond the brief.** Assign and close workflow with states (`OPEN`, `PENDING`, `CLOSED`), change own password, user list and role change for analysts, flash messages for errors, GitHub Actions CI with Ruff and the unit tests.

### 1.3 Technology

| Piece | Choice and reason |
| :--- | :--- |
| **Language and framework** | Python 3.11, Flask 3.0.3, Jinja2 templates |
| **Database** | **MariaDB.** Incidents, users, comments and attachments are related entities with foreign keys and `ON DELETE CASCADE`, and the list view needs joins (incident, creator, analyst, severity, state). A relational database gives that integrity without writing it by hand, and it is the persistence the later phases (containers, deployment) will need anyway. |
| **Driver** | PyMySQL 1.1.1 with parameterized queries |
| **Configuration** | python-dotenv, for database and session settings in a `.env` file. It also let us run the application on our personal devices during development, without depending on the production server. |
| **Linting** | Ruff, for naming conventions and a consistent code style, since we had limited time |
| **Testing** | Pytest |

> <span style="color:#2E75B6">**Note.**</span> We first used MariaDB to work with UUID values directly. We later realized that PyMySQL converts UUID values into strings automatically, so we did not need to handle that conversion ourselves.

#### Why we use parameterized queries

*Terminology: PyMySQL binds the `%s` values itself, on the client, before sending the query. This is called a parameterized query. It is not a server-side prepared statement, but it gives the same protection against injection for this application.*

Every SQL statement in the repositories sends the query text and the user's values **separately**, with `%s` placeholders:

```python
# What we do: the value travels apart from the query
cursor.execute("SELECT * FROM user WHERE email = %s", (email,))

# What we avoid: the value is glued into the query text
cursor.execute("SELECT * FROM user WHERE email = '" + email + "'")
```

The reasons:

1. **The database never mistakes data for code.** With string-building, an email such as `' OR '1'='1` becomes part of the SQL and changes what it does (SQL injection). With placeholders, that same text is only a value to compare, so it cannot change the query.
2. **It is just as easy to write.** It costs one extra argument per query, and it removes the need to escape quotes by hand, which is easy to forget.
3. **It handles special characters correctly.** Names such as `O'Brien` or titles with quotes work without errors.
4. **It keeps the layers clean.** The SQL lives only in the repositories, so the rule is applied in one place and the services and routes never build queries.
5. **It costs nothing later.** The handout allows string-built SQL in Phase 1 as a visible shortcut, but we did not take it: avoiding it was free, and the Phase 3 injection work then starts from a safe base instead of a rewrite.

> **Limit.** Parameters protect the *values* only. Table and column names cannot be parameterized, so if a future feature builds them from user input (for example a sort column), that input must be checked against a fixed list. Parameterized queries also do not protect against the other problems in this report, such as raw HTML in comments (shortcut #3).

---

## 2. Architecture

Sentinel follows the prescribed layered skeleton. **Each layer only talks to the one below it**, and `services/factory.py` is the only file that connects a service to its repository and to the database connection.

```
Browser ──▶ Routes ──▶ Services ──▶ Repositories ──▶ MariaDB
             (HTTP)    (rules)       (SQL only)
                ▲
          services/factory.py  (wires services to repositories)
```

### Rules that keep the layers separate

| Layer | Rule |
| :--- | :--- |
| **Routes** | Read the request, call one service and return a response. They render templates. They do not touch the database or the repositories. |
| **Factory** (`app/services/factory.py`) | The only place where services are connected to repositories and to the request's database connection. Routes ask the factory for a service. |
| **Services** | Hold the business rules (who can see, comment, assign or close). They receive plain values and return model objects. They raise `PermissionError`, `LookupError` or `ValueError`. Routes do not build HTML from them; `routes/common.py` turns those exceptions into HTTP 403, 404 and 400 responses. |
| **Repositories** | The only code that writes SQL. All of them inherit from `RepositoryABC`, an abstract base class with `get_by_id`, `create`, `update` and `delete`. |
| **Models** | Hold the data and the rules that protect it. Attributes that must only change through a method (for example `Incident.severity`, `state` and `analyst_id`) are read-only properties. |

### How it works

**Example: an analyst assigns an incident** (`POST /incidents/<id>/assign`, in `routes/incidents.py`)

1. The route asks the factory for `get_incident_service()`.
2. `IncidentService.assign_incident()` checks that the user is an analyst and that the incident is not already assigned to someone else.
3. `IncidentRepository.update()` saves the change.
4. The route redirects to the detail page.

---

## 3. Components

| Component | Location | Responsibility |
| :--- | :--- | :--- |
| **Entry point** | `run.py` | Creates the app and starts the server. |
| **Application factory** | `app/__init__.py` | Creates the Flask app, sets the session key and registers the blueprints and error handlers. |
| **Routes** | `app/routes/` | `auth.py` (login, register, password), `incidents.py` (list, create, detail, assign, close), `comments.py`, `attachments.py` (download), `users.py` (create users, change roles), `common.py` (home, current user, error handlers). |
| **Services** | `app/services/` | `UserService`, `IncidentService`, `CommentService`, `link_service.py` (fetches page titles), `factory.py` (builds the services). |
| **Models** | `app/models/` | `User` with subclasses `Analyst` and `Employee`; `Incident`; `Comment`; `Attachment` (it also writes and removes its own file on disk). |
| **Repositories** | `app/repositories/` | `RepositoryABC` and its three implementations: `UserRepository`, `IncidentRepository` (it also saves the attachment row in the same transaction as the incident) and `CommentRepository`. |
| **Database connection** | `app/db/database.py` | Opens one MySQL connection per request and closes it when the request ends. |
| **Schema and seed data** | `init.sql` | Tables and lookup values for severity and state, plus one initial analyst account. |
| **Views** | `app/templates/`, `app/static/` | Jinja2 pages, the CSS and the icon. |
| **Tests** | `tests/` | Unit tests in `tests/unit` (models, services, repositories) and functional tests in `tests/functional`, which use the real routes and templates with in-memory repositories. The CI runs Ruff and the unit tests. |

---

## 4. Deviations from the handout

The handout says what to build but leaves many rules open, and in a few places we chose something different from its literal wording. Each deviation is listed with the reason and what it costs us.

> A deviation is not a claim that the choice was right. It is the decision we can defend today.

### Deviation 1: Who can comment

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | “Any logged-in user can comment on an incident.” |
| <span style="color:#1F4E79">**We built**</span> | Only the creator of the incident and its assigned analyst can comment. |
| <span style="color:#548235">**Why**</span> | An incident report is confidential. Letting someone comment on an incident they are not allowed to see would contradict the visibility rule, so commenting follows the same rule as viewing. |
| <span style="color:#C00000">**Cost**</span> | An incident that nobody has claimed has no analyst comments until an analyst takes it. Phase 2 (who-sees-what) will review this rule. |

### Deviation 2: Who sees which incidents

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | “Incidents are stored and listed”, with no rule about who sees what. |
| <span style="color:#1F4E79">**We built**</span> | Employees see only their own incidents; analysts see all of them. |
| <span style="color:#548235">**Why**</span> | Incident reports are sensitive, and analysts need the whole queue to triage. It also gives Phase 2 an ownership rule to build on. |
| <span style="color:#C00000">**Cost**</span> | The rule lives in `IncidentService` and is only as strong as the login (shortcuts #1 and #2). |

### Deviation 3: Who can be an analyst

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | “Users can register and log in.” |
| <span style="color:#1F4E79">**We built**</span> | Anyone can register, but always as an employee. Only an analyst can create users or change a role. |
| <span style="color:#548235">**Why**</span> | If registration let people choose their role, anyone could make themselves an analyst and read every incident. |
| <span style="color:#C00000">**Cost**</span> | The first analyst must exist, so `init.sql` creates one with a known password (#2). Registration has no checks (#19) and any analyst can promote anyone (#20). |

### Deviation 4: Role names

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | Example hierarchy: `User → Analyst / Admin`. |
| <span style="color:#1F4E79">**We built**</span> | `User → Analyst / Employee`. |
| <span style="color:#548235">**Why**</span> | The handout gives Admin only as an example (“e.g.”). Employee and Analyst match the real people: employees report, analysts triage. The hierarchy and polymorphism are still shown. |
| <span style="color:#C00000">**Cost**</span> | There is no Admin: the analyst is the most powerful role. |

### Deviation 5: Assign and close workflow

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | Not requested. |
| <span style="color:#1F4E79">**We built**</span> | An analyst claims an incident; only the assigned analyst can close it. States: `OPEN`, `PENDING`, `CLOSED`. |
| <span style="color:#548235">**Why**</span> | Replacing the spreadsheet needs someone who owns each incident. It also gave us a real change of state to study for the concurrency topic. |
| <span style="color:#C00000">**Cost**</span> | Brings the race conditions #22 (assigning) and #23 (updating). |

### Deviation 6: Attachment

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | “One optional file per incident, uploaded and stored.” |
| <span style="color:#1F4E79">**We built**</span> | The file is attached only when the incident is reported, in the same database transaction. It cannot be added or replaced later. |
| <span style="color:#548235">**Why**</span> | A separate upload step could leave an incident without its file. A single moment to attach keeps the “one file” rule simple. |
| <span style="color:#C00000">**Cost**</span> | No way to change the file later; any type and size is accepted (#8). |

### Deviation 7: The `/health` route

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | R10: routes never touch the database. |
| <span style="color:#1F4E79">**We built**</span> | The `/health` route was removed. |
| <span style="color:#548235">**Why**</span> | It was the only route that used the database directly. |
| <span style="color:#C00000">**Cost**</span> | There is no health endpoint now; it would have to go through a service. |

### Deviation 8: Extra features

| | |
| :--- | :--- |
| <span style="color:#7F7F7F">**Handout**</span> | Not requested. |
| <span style="color:#1F4E79">**We built**</span> | Change own password, user list, role change, flash error messages, CI with Ruff and unit tests. |
| <span style="color:#548235">**Why**</span> | Analysts need to manage accounts without editing the database, and CI keeps the team's code consistent. |
| <span style="color:#C00000">**Cost**</span> | More code to secure in later phases. |

---

## 5. Shortcuts

Every item below exists in the code today and was left on purpose, as the handout asks (R19). Items **#22 to #27** are about concurrency: they work with one user at a time and fail when two requests overlap.

| # | Shortcut | Where | Why it matters later |
| :---: | :--- | :--- | :--- |
| **1** | Passwords stored and compared in plain text | `models/user.py`, `UserService.authenticate` and `change_password`, `init.sql` | A database leak exposes every password |
| **2** | Default analyst with a known password (`analyst@sentinel.local` / `analyst123`), also written in the README | `init.sql`, `README.md` | Anyone who reads the repository can log in as an analyst |
| **3** | Comments rendered as raw HTML (the `safe` filter) | `templates/incident.html`, line 52 | Stored XSS on every incident page |
| **4** | No input validation: lengths, formats and empty values are not checked; `int(severity)` and `UUID(analyst_id)` fail on bad input | `routes/incidents.py` | 500 errors and unexpected values reaching the database |
| **5** | The search loads all incidents and filters them in Python; the filter text is sent back to the page | `IncidentService.list_incidents`, `incidents.html` | Reflected input; poor scalability |
| **6** | The server fetches any URL the user pastes, with no allow-list, scheme check or internal-address block | `services/link_service.py` | SSRF |
| **7** | The fetched title is stored unsanitised and the link uses the raw user URL | `templates/incident.html` | `javascript:` links and stored injection |
| **8** | No validation of uploaded files: any type and size is accepted, and the MIME type comes from the client | `routes/incidents.py`, `IncidentService.create_incident` | Malicious uploads |
| **9** | Files are saved on the local disk (`ATTACHMENTS_DIR`) and sent with `send_file`; no scanning, no isolation | `models/attachment.py`, `routes/attachments.py` | Storage and path handling |
| **10** | No CSRF protection on any POST form | All POST routes | Forged requests |
| **11** | Logout is a GET request | `routes/auth.py` | Can be triggered by a link or an image tag |
| **12** | Session cookie defaults: no `Secure`, `HttpOnly` or `SameSite` settings; `SECRET_KEY` is not checked for existence or strength | `app/__init__.py` | Session theft or forgery |
| **13** | No brute-force protection: no rate limit, lockout or delay on login | `routes/auth.py` | Credential guessing |
| **14** | Debug mode on by default (`FLASK_ENV` other than `production`) | `run.py` | Interactive debugger exposed if deployed as is |
| **15** | Error handlers show the raw exception text in a flash message and redirect to the Referer header | `routes/common.py` | Internal messages leak; redirect target is controlled by the client |
| **16** | Database errors are printed to stdout and re-raised; no structured logging or audit trail | `repositories/` | No forensics |
| **17** | Database credentials in a plain `.env` file; one account with full rights | `db/database.py`, `env.example` | Least privilege |
| **18** | No HTTPS and no security headers (CSP, X-Frame-Options…) | Whole app | Traffic and clickjacking exposure |
| **19** | Public registration with no email check, no rate limit and no password rules | `POST /register`, `UserService.register` | Account spam, weak accounts |
| **20** | Any analyst can create analysts and change anyone's role; no approval step | `UserService.create_user` and `change_role` | Privilege escalation if one analyst is compromised |
| **21** | The preferences cookie is plain, unsigned text that the server trusts (`int(...)` on its value) | `list_incidents` in `routes/incidents.py` | A tampered cookie breaks the page; data is read back without checks |
| **22** | Check-then-act when assigning: the rule is checked on an old copy, so two analysts can claim the same incident and neither gets an error | `IncidentService.assign_incident`, `POST /incidents/<id>/assign` | Race condition; ownership lost silently |
| **23** | Lost update: the update writes four columns (severity, state, analyst, close date) from a stale copy, so a closed incident can reopen | `IncidentRepository.update` | One change silently erases another |
| **24** | Duplicate email is checked in code and then inserted; if two requests overlap, the second ends in an unhandled database error (HTTP 500) | `UserService._check_email_is_free`, `UserRepository.create` (`POST /register`, `POST /users/new`) | Relies only on `UNIQUE(email)`; the public sign-up makes it easier to hit |
| **25** | No protection against a double submit: two fast clicks create two identical incidents | `POST /incidents/new` | Duplicate records; replayed requests |
| **26** | The page title is fetched with a blocking call (5 s timeout) inside the request | `link_service.fetch_page_title`, called from `create_incident` | With one worker, a slow site stalls every user |
| **27** | The functional tests run only locally, and no test reproduces the race conditions above | `.github/workflows/ci.yml`, `tests/functional/` | Regressions go unnoticed |

---

## 6. Preliminary security analysis

We reviewed the whole application as built (routes, services, repositories, models, templates and configuration) by reading the code and following each input from the browser to the database and back.

> <span style="color:#C00000">**Limits.**</span> We did not attack the running application, and we did not audit the dependencies (Flask 3.0.3, PyMySQL 1.1.1, python-dotenv 1.0.1), so outdated libraries are marked “not assessed”.

### 6.1 What we protect and who can reach it

- **Assets:** user credentials, incident reports (confidential by nature), attachments, and the login session.
- **Who can reach the application:** an anonymous visitor (login and registration only), an employee, an analyst, and anyone on the network that can reach the server.

| Entry point | Who | What it accepts |
| :--- | :--- | :--- |
| `POST /login`, `POST /register` | Anonymous | Email, password, name |
| `GET /incidents` | Logged-in user | Title filter, severity (query or cookie), state |
| `POST /incidents/new` | Logged-in user | Title, description, severity, URL, uploaded file |
| `POST /incidents/<id>/comments` | Creator or assigned analyst | Free text |
| `POST /incidents/<id>/assign`, `/close` | Analyst | A user id |
| `GET /incidents/<id>/attachment` | Anyone who can see the incident | Incident id |
| `POST /users/new`, `POST /users/<id>/role` | Analyst | Name, email, password, role |
| `GET /logout`, `POST /password` | Logged-in user | Passwords |

### 6.2 What already helps

These are real strengths of the current design. They do not make the application secure, but they mean some classic problems are not present.

- **No string-built SQL.** Every query uses bound parameters (`%s`), so the usual SQL injection through form fields does not apply.
- **Output escaping is on by default.** Jinja2 escapes every value except the comments (shortcut #3), so titles, descriptions, names and the fetched page title are not executed as HTML.
- **Permission checks live in the services.** An employee only sees their own incidents; comments, attachments and the incident detail all go through the same visibility check, so changing the id in the URL does not expose someone else's incident.
- **Ids cannot be guessed in sequence.** Incidents and users use UUIDs.
- **Uploaded file names are not trusted.** The stored name is generated from the attachment's own id plus the extension, so a name such as `../x` cannot choose where the file is written, and the file is created with mode `'xb'`, which never overwrites.
- **The user is re-read from the database on every request,** so a role change or a deleted account takes effect immediately.
- **Registration always creates an employee,** and the role is validated against a fixed list, so a form cannot request the analyst role directly.
- **Changing the password requires the current one.**
