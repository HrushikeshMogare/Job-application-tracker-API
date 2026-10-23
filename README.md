# Job Application Tracker API

A Django REST Framework backend for managing job applications, interviews and follow-up reminders.
It is a learning project, built to run locally. It has not been deployed to the cloud.

## What is included

| Blueprint phase | In this project |
|---|---|
| 01 Foundation | Django project, Git-ready layout, `.gitignore` |
| 02 Data | Models for Company, JobApplication, Interview, Reminder, with migrations (PostgreSQL, SQLite fallback) |
| 03 API | Serializers, viewsets, routers, full CRUD |
| 04 Security | JWT login (access + refresh), per-user data isolation, validation, throttling |
| 05 Advanced features | Search, filtering, ordering, pagination, dashboard statistics |
| 06 Quality | 42 pytest tests (CRUD, auth, permissions, validation, reminders task) |
| 07 Async tasks | Celery task + Celery beat schedule, Redis broker, reminder emails |
| 08 DevOps | Dockerfile, Docker Compose (web, db, redis, worker, beat), Jenkinsfile |
| 09 Deployment | Environment-variable config, OpenAPI docs at `/api/docs/`. Cloud hosting is NOT included. |

## Run it locally (quickest: SQLite, no Docker)

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser    # optional, for /admin/
python manage.py runserver
```

Open http://127.0.0.1:8000/api/docs/ for interactive API documentation.

Run the tests:

```bash
python -m pytest
```

## Run with PostgreSQL, Redis and Celery (Docker)

```bash
cp .env.example .env     # then edit the secret key and database password
docker compose up --build
```

The API is at http://localhost:8000. Reminder emails are printed to the `worker` container log
(console email backend) each time Celery beat runs the task (every 5 minutes).

## Using the API (Postman or curl)

1. Register: `POST /api/auth/register/` with `{"username","email","password"}`
2. Log in: `POST /api/auth/token/` with `{"username","password"}` returns `access` and `refresh`
3. Send `Authorization: Bearer <access>` on every other request
4. Access tokens last 15 minutes. Get a new one with `POST /api/auth/token/refresh/` and `{"refresh": "..."}`

Create a company first, then an application that points at it:

```bash
curl -X POST localhost:8000/api/companies/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"name": "Example Technologies"}'

curl -X POST localhost:8000/api/applications/ -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Python Backend Developer", "company": 1, "status": "applied"}'
```

## Endpoints

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/token/`, `/api/auth/token/refresh/` | Public. JWT login and refresh |
| GET | `/api/auth/me/` | Current user |
| CRUD | `/api/companies/` | `?search=` |
| CRUD | `/api/applications/` | `?status=`, `?company=`, `?applied_after=`, `?applied_before=`, `?search=`, `?ordering=`, `?page=` |
| CRUD | `/api/interviews/` | `?application=`, `?interview_type=` |
| CRUD | `/api/reminders/` | `?application=`, `?is_completed=`, `?reminder_type=` |
| POST | `/api/reminders/{id}/complete/` | Mark done |
| GET | `/api/dashboard/stats/` | Totals by status, upcoming interviews, overdue reminders |

Statuses: `applied`, `assessment`, `interview`, `offer`, `rejected`. Any status can be set at any time,
because real applications do not follow one fixed path.

## Security notes

- Every record belongs to a user. Querysets are filtered by the logged-in user, so someone else's record
  returns 404. Related IDs (company, application) are also checked, so you cannot link to another user's data.
- JWT only proves who the caller is. Security also comes from hashed passwords, password validation,
  input validation, ownership checks, throttling, and keeping secrets in environment variables.
- Before any real deployment: set a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, a real `ALLOWED_HOSTS`,
  serve over HTTPS, and use a real email backend. These are not configured for you.

## CI/CD (Jenkins)

The `Jenkinsfile` defines: checkout, install dependencies, run tests, build Docker image, deploy with
Docker Compose on the same machine. Point a GitHub webhook at Jenkins (use ngrok if Jenkins runs locally).
The agent needs Python 3.12, Docker and Docker Compose.

## Project layout

```
config/      settings, urls, Celery app
accounts/    register, me, JWT routes
tracker/     models, serializers, views, filters, tasks, tests
Dockerfile, docker-compose.yml, Jenkinsfile, requirements.txt, pytest.ini, .env.example
```
