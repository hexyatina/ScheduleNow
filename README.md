# ScheduleNow - FastAPI Schedule Manager

A FastAPI-based schedule management service with PostgreSQL, JWT authentication, role-based access, web calendar UI, and optional .ics email invitations.

## Start with Docker

1. Clone the repository and configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to set a `SECRET_KEY`, `DB_PASSWORD`, and SMTP credentials for email notifications.

2. Start the application and PostgreSQL:
   ```bash
   docker compose up -d --build
   ```

3. Open the app:
   - Calendar UI: http://localhost:8000/calendar
   - Swagger API Docs: http://localhost:8000/docs

## Initial Setup (Admin / Demo Data)

Create the first manager or superadmin user interactively:
```bash
docker compose exec app python create_manager.py
```

Or seed sample users, groups, locations, and events (**warning: drops and recreates all tables**):
```bash
docker compose exec app python reset_and_seed.py
```

## Stopping & Logs

```bash
# View logs
docker compose logs -f app

# Stop containers (keeps database data)
docker compose down

# Stop and remove database volume
docker compose down -v
```

## Local Development (without Docker)

Requires Python 3.12+ and a running PostgreSQL instance:

```bash
pip install -r requirements.txt
cp .env.example .env
# Set DB_HOST=localhost in .env
uvicorn main:app --reload
```

## Or try and see for yourself by going into this website:
https://schedule-now.app
