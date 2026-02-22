# Board Game Session Tracker

## Run Full Stack with Docker (Backend + Frontend + DB)

```bash
docker compose up --build
```

Open:

- Backend docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Local Development Setup

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

Verify the container is healthy:

```bash
docker compose ps
```

You should see `board_game_tracker-db-1` with status `healthy`.

### 2. Set DATABASE_URL

The backend reads `DATABASE_URL` from the environment. When running inside Docker Compose this is set automatically. When running outside Docker, export it manually:

```bash
# Format: postgresql://<user>:<password>@<host>:<port>/<database>
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/board_game_tracker
```

> **Note:** Use `localhost` when running outside Docker and `db` when running inside Docker Compose (the service name acts as the hostname).

### 3. Start the Backend

**Option A — via Docker Compose (recommended):**

```bash
docker compose up -d
```

**Option B — locally (requires Python 3.12+ and pip):**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Verify DB Connectivity

**curl:**

```bash
curl http://localhost:8000/health-db
# Expected: {"status":"ok","database":"connected"}
```

**psql (from host):**

```bash
psql postgresql://postgres:postgres@localhost:5432/board_game_tracker -c "SELECT 1;"
```

**psql (inside the container):**

```bash
docker compose exec db psql -U postgres -d board_game_tracker -c "SELECT 1;"
```

---

## Troubleshooting

### Database not ready / connection refused

The backend depends on the `db` service healthcheck, but if you start the backend outside Docker it may try to connect before Postgres is ready.

```
psycopg2.OperationalError: connection refused
```

**Fix:** Wait for the healthcheck to pass before starting the backend:

```bash
docker compose up -d db
docker compose exec db pg_isready -U postgres   # repeat until "accepting connections"
```

### Wrong DATABASE_URL driver prefix

SQLAlchemy requires the `postgresql://` prefix. The older `postgres://` prefix will fail:

```
sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres
```

**Fix:** Make sure your URL starts with `postgresql://`, not `postgres://`:

```
# Wrong
postgres://postgres:postgres@localhost:5432/board_game_tracker

# Correct
postgresql://postgres:postgres@localhost:5432/board_game_tracker
```

### Missing psycopg2 driver

If you see this error when starting the backend locally:

```
ModuleNotFoundError: No module named 'psycopg2'
```

**Fix:** Install the binary package:

```bash
pip install psycopg2-binary
```

This is already included in `requirements.txt` but may be missing if you installed dependencies in a different virtual environment.
