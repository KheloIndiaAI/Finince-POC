# Local Setup & Deployment

## Schema changes (no migration tool yet — MVP, deferred on purpose)
`init_db()` (app/db.py) only calls `Base.metadata.create_all`, which creates
MISSING TABLES, not missing COLUMNS on a table that already exists. If a
change adds/renames a column on an existing table (e.g. the
`remarks_snippet` column added to `comparison_extractions`), an already-running
dev Postgres needs a manual `ALTER TABLE`, or you drop the container's volume
and let it recreate the schema from scratch (fine while it's just test data):
```
docker compose down -v   # drops the postgres volume too - test data is lost
docker compose up -d --build
```
or, without losing existing rows:
```sql
ALTER TABLE comparison_extractions ADD COLUMN remarks_snippet TEXT DEFAULT '';
ALTER TABLE comparison_extractions ADD COLUMN uc_purpose_snippet TEXT DEFAULT '';
```
Once real data matters, this is exactly the point to bring in Alembic.

## Run with Docker (Postgres + backend)
1. Fill the env files (secrets are NOT committed):
   - `cp .env.example .env`                 # Postgres creds
   - `cp backend/.env.example backend/.env` # app config (DB_*, AWS, Bedrock)
   - keep `DB_*` in `backend/.env` matching `POSTGRES_*` in `.env`
2. `docker compose up -d --build`
3. Open http://localhost:8000/health and http://localhost:8000/docs

## Run backend alone (dev, needs a reachable Postgres)
1. `docker compose up -d postgres`
2. `cd backend`
3. `python -m venv venv` and activate it (`venv\Scripts\activate` on Windows)
4. `pip install -r requirements.txt`
5. `python run.py` (same as `uvicorn app.main:app --reload`, easier to remember).
   `run.py` loads `backend/.env` into the environment so boto3 finds the AWS keys —
   Docker does this via `env_file`, the host path needs it done here.

`backend/.env` ships with `DB_HOST=localhost` / `DB_PORT=55433`: compose publishes
the Postgres container on host port 55433, because 5432 and 5433 are taken by
native Postgres services on some dev machines. The `backend` service in
docker-compose.yml overrides both to `postgres:5432`, so the same `.env` works for
Docker and for `python run.py` with nothing to toggle.

## Run the tests
    cd backend
    pip install -r requirements.txt
    pytest -q
requirements.txt has one list (pytest + httpx included — this is a small MVP,
not worth a separate dev-requirements file). No AWS and no Postgres needed —
S3, Textract, and Bedrock are stubbed via the fixtures in `tests/conftest.py`;
the DB is an in-memory SQLite.

## Live smoke test (once the stack is up)
    curl -s -X POST http://localhost:8000/api/comparisons \
      -F "sanction_file=@sanction.pdf;type=application/pdf" \
      -F "expenditure_file=@uc.pdf;type=application/pdf"
    aws s3 ls s3://finance-poc-1/comparisons/ --recursive

## Run the frontend (dev)
1. `cd frontend`
2. `npm install`
3. `cp .env.example .env` and set `VITE_API_BASE_URL` if the backend isn't
   on `http://localhost:8000`
4. `npm run dev` -> opens on http://localhost:5173
The app is a single page: upload the two PDFs, review/correct the 3
extracted fields, confirm, then see the result with Regenerate Summary and
version history.

## Deployment target: AWS EC2 + Docker Compose
- One EC2 (Ubuntu) running Docker Compose: `postgres` + `backend`.
- Backend reaches Postgres by the compose service name `postgres`
  (`DB_HOST=postgres`) — never `localhost` or the EC2 IP.
- Two env files, both git-ignored:
    - `./.env`          Postgres container creds (POSTGRES_DB/USER/PASSWORD)
    - `./backend/.env`  app config (DB_*, AWS, Bedrock)
- After pulling code changes on the EC2, rebuild before testing:
  `docker compose up -d --build`.
