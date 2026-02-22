# Backend Testing

## Requirements

- Docker Desktop running
- PostgreSQL available (recommended via Docker Compose)
- Python 3.12+

## Run Tests Locally (PowerShell)

1. Start Postgres:

```powershell
docker compose up -d db
```

2. Set required environment variables:

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/board_game_tracker_test"
$env:JWT_SECRET_KEY="local-test-secret"
$env:CORS_ORIGINS="*"
```

3. Install backend + test dependencies:

```powershell
pip install -r backend/requirements.txt
pip install -r backend/requirements-test.txt
```

4. Run tests:

```powershell
pytest -q backend/tests
```

## Notes

- Tests run against the database from `DATABASE_URL`.
- Tests automatically apply Alembic migrations before execution.
- Tables are truncated between tests so local DB state does not affect test results.
