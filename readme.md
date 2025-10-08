# Videoflix Backend

_Django + DRF backend for video uploads, background processing with RQ/Redis, and HLS streaming.  
User emails (activation & password reset) are sent **asynchronously** via the same queue._

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.x-092E20)
![DRF](https://img.shields.io/badge/DRF-3.x-red)
![Redis](https://img.shields.io/badge/Redis-RQ-DC382D)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Quick Start (Docker)](#quick-start-docker)
- [Install Packages](#install-packages)

---

## Features

- **JWT auth** (SimpleJWT)
- **Background jobs** with **Django-RQ** (worker launched from the web container entrypoint)
- **FFmpeg** HLS pipeline (360p/480p/720p/1080p), thumbnails, metadata
- Endpoints to serve **HLS manifests** and **TS segments**
- **Queued emails** for account activation & password reset
- Test suite for critical endpoints (auth required, content types, 200/404 cases)

---

## Tech Stack

- Python / Django / Django REST Framework
- Redis + RQ (via `django-rq`)
- PostgreSQL
- Gunicorn
- Docker Compose

---

## Prerequisites

- Docker & Docker Compose
- (Optional) Postman / REST Client for quick checks

---

## Configuration

Create your environment file (dot-env) from the template:

```bash
cp .env.template .env
```

Set (at least) the following variables: <br>
"change-me" indicates a placeholder. Replace it with the appropriate value for your project setup.

| Key                       | Example                                     | Notes                                                                                                                                                  |
| :------------------------ | :------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------- |
| DJANGO_SUPERUSER_USERNAME | change-me                                   | default: admin                                                                                                                                         |
| DJANGO_SUPERUSER_EMAIL    | change-me                                   | default: admin@example.com                                                                                                                             |
| SECRET_KEY                | change-me                                   | Any non-empty string; You can generate one with ```python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())```"                                                                                                                            |
| DJANGO_SUPERUSER_PASSWORD | change-me                                   | default: adminpassword                                                                                                                                 |
| DEBUG                     | True                                        | False for production                                                                                                                                   |
| ALLOWED_HOSTS             | localhost,127.0.0.1                         |                                                                                                                                                        |
| CSRF_TRUSTED_ORIGINS      | http://localhost:5500,http://127.0.0.1:5500 | separated by commas, without spaces                                                                                                                    |
| FRONTEND_ORIGIN           | http://127.0.0.1:5500                       | Don't use localhost – it's incompatible with the frontend.                                                                                             |
| BASE_BACKEND_URL          | http://127.0.0.1:8000                       | Don't use localhost – it's incompatible with the frontend.                                                                                             |
| DOCKER_VOLUME | .:/app | Use this value in development. Leave it empty in production. |
| DB_NAME                   | change-me                                   | Any string will work.                                                                                                                                  |
| DB_USER                   | change-me                                   | Any string will work.                                                                                                                                  |
| DB_PASSWORD               | change-me                                   | Any string will work. **Make sure to choose a secure password.**                                                                                       |
| DB_HOST                   | db                                          |                                                                                                                                                        |
| DB_PORT                   | 5432                                        |                                                                                                                                                        |
| REDIS_HOST                | redis                                       |                                                                                                                                                        |
| REDIS_LOCATION            | redis://redis:6379/1                        |                                                                                                                                                        |
| REDIS_PORT                | 6379                                        |                                                                                                                                                        |
| REDIS_DB                  | 0                                           |                                                                                                                                                        |
| EMAIL_HOST                | smtp.example.com                            | SMTP server hostname of your email provider (e.g., smtp.web.de, smtp.gmail.com). Check your provider’s docs for the correct port and TLS/SSL settings. |
| EMAIL_PORT                | 587                                         |                                                                                                                                                        |
| EMAIL_HOST_USER           | change-me                                   |                                                                                                                                                        |
| EMAIL_HOST_PASSWORD       | your_email_user_password                    |                                                                                                                                                        |
| EMAIL_USE_TLS             | True                                        |                                                                                                                                                        |
| EMAIL_USE_SSL             | False                                       |                                                                                                                                                        |
| DEFAULT_FROM_EMAIL        | default_from_email                          |                                                                                                                                                        |

Note: RQ_QUEUES is configured in settings.py (host/port/db + default timeout). No changes required.

# Quick Start (Docker)

Use either docker compose or docker-compose depending on your system.

# Build & start all services (web runs the rqworker from its entrypoint)

docker compose up -d --build

# Follow logs (you should see: \*\*\* Listening on default...)

docker compose logs -f web

# Install packages

docker-compose exec web pip install -r requirements.txt

# Perform unit tests
This project includes a test suite to verify core functionality (authentication, password reset, API endpoints). 
Tests run in an isolated test database and can be executed as follows:

### In Docker (recommended):

Run all tests with the following command:

```bash
docker compose exec web python manage.py test
```

If you want additional text for further reference run

```bash
docker compose exec web python manage.py test -v 2
```
If you want to run test of a certain app, use 
```bash
docker compose exec web python manage.py test <app-name>
```
Replace <app-name> by the app in question, e.g. user_auth_app

If you want to run tests of a certain class, use 
```bash
docker compose exec web python manage.py test <app-name>.api.tests.test_views.<ClassName>
```
Replace <app-name> and <ClassName> accordingly, e.g video_app and VideoListViewTest.