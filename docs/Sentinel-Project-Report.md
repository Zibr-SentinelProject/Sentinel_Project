# 

# **SENTINEL REPORT**

**PROGRAMME:** Informazioaren teknologien inguruneetan zibersegurtasun

**MODULE:** EKOS

**AUTHOR:** Daniel Alvarez

 Yaxche Alvarez

Wara Pacheco

**DATE:** 04/10/2026

# 

# **INDEX** {#index}

[**INDEX	2**](#index)

[**1\. APPLICATION OVERVIEW	3**](#1.-application-overview)

[1.1. Users	3](#1.1.-users)

[1.2. Features	3](#1.2.-features)

[1.3. Technology	4](#1.3.-technology)

[**2\. ARCHITECTURE	4**](#2.-architecture)

[**3\. COMPONENTS	5**](#3.-components)

[**4\. SHORTCUTS	7**](#4.-shortcuts)

[**4\. Deviation log and second thoughts	8**](#5.-preliminary-security-analysis)

[**7\. Preliminary security analysis	12**](#heading=h.5s2ih245t7q1)

[7.1 What we protect and who can reach it	12](#5.1-what-we-protect-and-who-can-reach-it)

[7.2 Findings by area	13](#5.2.-what-already-helps)

[7.3. What already helps	15](#heading=h.q1ti9yqwqjy0)

# 

# **1\. APPLICATION OVERVIEW** {#1.-application-overview}

Sentinel is an internal web application for Nexus Digital Solutions that replaces the shared spreadsheet, email and chat used so far to track security incidents. Employees report incidents; analysts triage, assign, discuss and close them.

## **1.1. Users** {#1.1.-users}

| Role | What they can do? |
| :---- | :---- |
| Employee | Register, report incidents, see and comment on their own incidents, attach one file when they report an incident. |
| Analyst | Everything an employee can do on their own incidents, plus see every incident, assign (claim) an incident, close the incidents assigned to them, create users with any role, list users and change roles |

## **1.2. Features** {#1.2.-features}

- Registration, login and logout. Anyone can register, and all new accounts are created with the employee role.  
- Incident report form: title, description, severity, optional external link and optional file attachment.  
- Incident list: incidents are displayed from newest to oldest, with a title search and a severity filter.  
- Saved filter: the selected severity filter is stored in a cookie and automatically applied the next time the incident list is opened.  
- Incident detail view: displays the incident information, comments, attachment, source link and available management actions.  
- Comments: both the incident creator and the assigned analyst can add comments.  
- Attachments: each incident can have one optional attachment. It is uploaded when the incident is created and cannot be added later. Users with permission to view the incident can also download its attachment.  
- Source link: the server fetches the external page and stores its HTML \<title\> to display it with the incident.  
- User management (analysts only): analysts can create users and change their roles.  
- Extra features beyond the brief: assign and close workflow with states (OPEN, PENDING, CLOSED), change own password, user list and role change for analysts, flash messages for errors, GitHub Actions CI with Ruff and the unit tests.

## **1.3. Technology** {#1.3.-technology}

- Python 3.11, Flask 3.0.3, and Jinja2 templates.  
- MariaDB: Incidents, users, comments and attachments are related entities with foreign keys and ON DELETE CASCADE, and the list view needs joins (incident, creator, analyst, severity, state). A relational database gives that integrity without writing it by hand, and it is the persistence the later phases (containers, deployment) will need anyway.

  We used MariaDB to work with UUID values directly. However, we later realized that PyMySQL automatically converts UUID values into strings, so we did not need to handle this conversion ourselves.

- PyMySQL 1.1.1 using parameterized queries  
- python-dotenv to manage database and session settings through a .env file. It also allowed us to run the application on our personal devices during development, without depending on the production server  
- Ruff for linting and code formatting. Since we had limited time, we used a linter to help us follow naming conventions and maintain consistent code style.  
- Pytest for testing the application.

# **2\. ARCHITECTURE** {#2.-architecture}

Sentinel follows the prescribed layered skeleton. Each layer only talks to the one below it, and services/factory.py is the only file that connects a service to its repository and to the database connection.

Rules that keep the layers separate:

- Routes read the request, call one service and return a response. They render templates. They do not touch the database or the repositories.  
- Factory (app/services/factory.py) is the only place where services are connected to repositories and to the request's database connection. Routes ask the factory for a service.  
- Services hold the business rules (who can see, comment, assign or close). They receive plain values and return model objects. They raise PermissionError, LookupError or ValueError. Routes do not build HTML from them; routes/common.py turns those exceptions into HTTP 403, 404 and 400 responses.  
- Repositories are the only code that writes SQL. All of them inherit from RepositoryABC, an abstract base class with get\_by\_id, create, update and delete.  
- Models hold the data and the rules that protect it. Attributes that must only change through a method (for example Incident.severity, state and analyst\_id) are read-only properties.

**How it works?**

Example: an analyst assigns an incident. 

**POST /incidents/\<id\>/assign (routes/incidents.py)** 

- Goes to get\_incident\_service() from the factory  
- Then IncidentService.assign\_incident() checks that the user is an analyst and that the incident is not already assigned to someone else.  
- Then IncidentRepository.update() saves the change  
- Finally, the route redirects to the detail page.

# **3\. COMPONENTS** {#3.-components}

| Component | Location | Responsibility |
| ----- | ----- | ----- |
| **Entry point** | run.py | Creates the app and starts the server. |
| **Application factory** | app/\_\_init\_\_.py | Creates the Flask app, sets the session key and registers the blueprints and error handlers. |
| **Routes** | app/routes/ | auth.py (login, register, password), incidents.py (list, create, detail, assign, close), comments.py, attachments.py (download), users.py (create users, change roles), common.py (home, current user, error handlers). |
| **Services** | app/services/ | UserService, IncidentService, CommentService, link\_service.py (fetches page titles), factory.py (builds the services). |
| **Models** | app/models/ | User with subclasses Analyst and Employee; Incident; Comment; Attachment (it also writes and removes its own file on disk). |
| **Repositories** | app/repositories/ | RepositoryABC and its three implementations: UserRepository, IncidentRepository (it also saves the attachment row in the same transaction as the incident) and CommentRepository. |
| **Database connection** | app/db/database.py | Opens one MySQL connection per request and closes it when the request ends. |
| **Schema and seed data** | init.sql | Tables and lookup values for severity and state, plus one initial analyst account. |
| **Views** | app/templates/, app/static/ | Jinja2 pages and the CSS and icon. |
| **Tests** | tests/ | Unit tests in tests/unit (models, services, repositories) and functional tests in tests/functional, which use the real routes and templates with in-memory repositories. The CI runs Ruff and the unit tests. |

# **4\. SHORTCUTS** {#4.-shortcuts}

# **5\. Preliminary security analysis** {#5.-preliminary-security-analysis}

We reviewed the whole application as built in (routes, services, repositories, models, templates and configuration) by reading the code and following each input from the browser to the database and back. 

We did not attack the running application, and we did not audit the dependencies (Flask 3.0.3, PyMySQL 1.1.1, python-dotenv 1.0.1), so outdated libraries are marked “not assessed”. 

## **5.1 What we protect and who can reach it** {#5.1-what-we-protect-and-who-can-reach-it}

**Assets:** user credentials, incident reports (confidential by nature), attachments, and the login session.

**Who can reach the application:** an anonymous visitor (login and registration only), an employee, an analyst, and anyone on the network that can reach the server.

| Entry point | Who | What it accepts |
| ----- | ----- | ----- |
| **POST /login, POST /register** | Anonymous | Email, password, name |
| **GET /incidents** | Logged-in user | Title filter, severity (query or cookie), state |
| **POST /incidents/new** | Logged-in user | Title, description, severity, URL, uploaded file |
| **POST /incidents/\<id\>/comments** | Creator or assigned analyst | Free text |
| **POST /incidents/\<id\>/assign, /close** | Analyst | A user id |
| **GET /incidents/\<id\>/attachment** | Anyone who can see the incident | Incident id |
| **POST /users/new, POST /users/\<id\>/role** | Analyst | Name, email, password, role |
| **GET /logout, POST /password** | Logged-in user | Passwords |

## **5.2. What already helps** {#5.2.-what-already-helps}

- These are real strengths of the current design. They do not make the application secure, but they mean some classic problems are not present.  
- No string-built SQL. Every query uses bound parameters (%s), so the usual SQL injection through form fields does not apply.  
- Output escaping is on by default. Jinja2 escapes every value except the comments (shortcut \#3), so titles, descriptions, names and the fetched page title are not executed as HTML.  
- Permission checks live in the services. An employee only sees their own incidents; comments, attachments and the incident detail all go through the same visibility check, so changing the id in the URL does not expose someone else’s incident.  
- Ids cannot be guessed in sequence. Incidents and users use UUIDs.  
- Uploaded file names are not trusted. The stored name is generated from the attachment’s own id plus the extension, so a name such as ../x cannot choose where the file is written, and the file is created with mode 'xb', which never overwrites.  
- The user is re-read from the database on every request, so a role change or a deleted account takes effect immediately.  
- Registration always creates an employee, and the role is validated against a fixed list, so a form cannot request the analyst role directly.  
- Changing the password requires the current one.

## **7.3. Deviation log and second thoughts**

Every gap between our code and the handout, and every change of mind, is logged with the decision, the reason and the cost. IDs (D1–D11) are referenced from the status table. The “Why” column is what we can defend today; it is not a claim that the first choice was right.

| \# | Shortcut | Where | Why it matters later |
| :---: | ----- | ----- | ----- |
| **1** | Passwords stored and compared in plain text | models/user.py, UserService.authenticate and change\_password, init.sql | A database leak exposes every password  |
| **2** | Default analyst with a known password (analyst@sentinel.local / analyst123), also written in the README | init.sql, README.md | Anyone who reads the repository can log in as an analyst |
| **3** | Comments rendered as raw HTML (the safe filter) | templates/incident.html, line 52 | Stored XSS on every incident page |
| **4** | No input validation: lengths, formats and empty values are not checked; int(severity) and UUID(analyst\_id) fail on bad input | routes/incidents.py | 500 errors and unexpected values reaching the database |
| **5** | The search loads all incidents and filters them in Python; the filter text is sent back to the page | IncidentService.list\_incidents, incidents.html | Reflected input; poor scalability |
| **6** | The server fetches any URL the user pastes, with no allow-list, scheme check or internal-address block | services/link\_service.py | SSRF  |
| **7** | The fetched title is stored unsanitised and the link uses the raw user URL | templates/incident.html | javascript: links and stored injection |
| **8** | No validation of uploaded files: any type and size is accepted, and the MIME type comes from the client | routes/incidents.py, IncidentService.create\_incident | Malicious uploads  |
| **9** | Files are saved on the local disk (ATTACHMENTS\_DIR) and sent with send\_file; no scanning, no isolation | models/attachment.py, routes/attachments.py | Storage and path handling  |
| **10** | No CSRF protection on any POST form | All POST routes | Forged requests  |
| **11** | Logout is a GET request | routes/auth.py | Can be triggered by a link or an image tag |
| **12** | Session cookie defaults: no Secure, HttpOnly or SameSite settings; SECRET\_KEY is not checked for existence or strength | app/\_\_init\_\_.py | Session theft or forgery  |
| **13** | No brute-force protection: no rate limit, lockout or delay on login | routes/auth.py | Credential guessing |
| **14** | Debug mode on by default (FLASK\_ENV other than production) | run.py | Interactive debugger exposed if deployed as is |
| **15** | Error handlers show the raw exception text in a flash message and redirect to the Referer header | routes/common.py | Internal messages leak; redirect target is controlled by the client |
| **16** | Database errors are printed to stdout and re-raised; no structured logging or audit trail | repositories/ | No forensics  |
| **17** | Database credentials in a plain .env file; one account with full rights | db/database.py, env.example | Least privilege |
| **18** | No HTTPS and no security headers (CSP, X-Frame-Options…) | Whole app | Traffic and clickjacking exposure |
| **19** | Public registration with no email check, no rate limit and no password rules | POST /register, UserService.register | Account spam, weak accounts |
| **20** | Any analyst can create analysts and change anyone’s role; no approval step | UserService.create\_user and change\_role | Privilege escalation if one analyst is compromised |
| **21** | The preferences cookie is plain, unsigned text that the server trusts (int(...) on its value) | list\_incidents in routes/incidents.py | A tampered cookie breaks the page; data that is read back without checks  |
| **22** | Check-then-act when assigning: the rule is checked on an old copy, so two analysts can claim the same incident and neither gets an error | IncidentService.assign\_incident, POST /incidents/\<id\>/assign | Race condition; ownership lost silently |
| **23** | Lost update: the update writes four columns (severity, state, analyst, close date) from a stale copy, so a closed incident can reopen | IncidentRepository.update | One change silently erases another |
| **24** | Duplicate email is checked in code and then inserted; if two requests overlap, the second ends in an unhandled database error (HTTP 500\) | UserService.\_check\_email\_is\_free, UserRepository.create (POST /register, POST /users/new) | Relies only on UNIQUE(email); the public sign-up makes it easier to hit |
| **25** | No protection against a double submit: two fast clicks create two identical incidents | POST /incidents/new | Duplicate records; replayed requests  |
| **26** | The page title is fetched with a blocking call (5 s timeout) inside the request | link\_service.fetch\_page\_title, called from create\_incident | With one worker, a slow site stalls every user  |
| **27** | The functional tests run only locally, and no test reproduces the race conditions above | .github/workflows/ci.yml, tests/functional/ | Regressions go unnoticed |

# 