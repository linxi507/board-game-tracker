# Board Game Session Tracker

## Run Full Stack with Docker (Backend + Frontend + DB)

```bash
docker compose up --build
```

Open:

- Backend docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

## Google Auth

Required backend env vars:

```bash
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

Google Cloud Console redirect URIs:

- Local backend callback: `http://localhost:8000/auth/google/callback`
- Render backend callback: `https://board-game-tracker-0.onrender.com/auth/google/callback`

Frontend URLs:

- Local frontend: `http://localhost:5173`
- Render frontend: `https://board-game-tracker-0.onrender.com`

Local manual verification:

1. Confirm local login still works with username/email + password.
2. Click `Continue with Google` on the login page.
3. Approve the Google consent screen.
4. Verify the browser lands on `/auth/callback`, then redirects to `/dashboard`.
5. Log out and repeat Google login; the same app user should be reused.

Render deployment notes:

1. Set `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, and `FRONTEND_URL` in Render.
2. Run the release command:

```bash
alembic upgrade head && python -m app.scripts.seed_top100_board_games
```

3. Verify local login still works, then verify Google login from the deployed login page.

## Board Game Catalog Seeding

Seed the global board game catalog manually (recommended):

```bash
docker compose exec backend python -m app.scripts.seed_board_games
```

Seed the Top 100 starter catalog:

```bash
docker compose exec backend python -m app.scripts.seed_top100_board_games
```

Render one-time seed command (Shell):

```bash
python -m app.scripts.seed_top100_board_games
```

Recommended Render release command:

```bash
alembic upgrade head && python -m app.scripts.seed_top100_board_games
```

Optional startup seeding:

```bash
# enables seed on API startup
SEED_ON_STARTUP=true
```

BGG CSV import skeleton (manual only):

```bash
docker compose exec backend python -m app.scripts.import_bgg_rank_csv
```

Set `BGG_RANKS_CSV_URL` before running the import script.

### Verify Search + Favorites + Custom Games

```bash
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_top100_board_games
```

Search API example:

```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/board-games?q=Root&limit=50&offset=0"
```

Verify catalog size (should return at least 50 rows on first page once seeded):

```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/board-games?limit=50&offset=0"
```

Manual smoke checklist:

1. Login in the frontend.
2. In Log Session search, type `Root` and verify it appears in dropdown.
3. Select `Root` and submit a session; verify it appears in Recent Sessions.
4. Click star on a global game and verify it appears in My Collection favorites.
5. Type a nonsense game name; verify `Add as custom game` appears.
6. Add custom game and select it; submit session and verify it appears as custom in Recent Sessions.
7. Delete a custom game from My Collection and verify it disappears from `/board-games` search results immediately.

### Verify Board Game Paging + Custom Game Delete

1. Login and open Dashboard.
2. In Network tab, search `a` in Log Session and verify:
   - `GET /board-games?q=a&limit=20&offset=0` returns up to 20 items.
3. Click `Load more` in the dropdown and verify:
   - next request uses `offset=20` and appends results.
4. In `My Collection` -> `Custom Games`, click `Delete` on a custom game:
   - not referenced by sessions -> deleted successfully.
   - referenced by sessions -> API returns `409` and UI shows a friendly message.

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
