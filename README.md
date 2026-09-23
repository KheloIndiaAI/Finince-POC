# Sanction vs UC (Expenditure) Comparison

Upload a Sanction Order and its Utilization Certificate (UC); the system extracts
the sanctioned amount, the utilized amount, and the expenditure type, then explains
in plain sentences whether the spending matches the sanction.

Read **CLAUDE.md** before changing code — it holds the engineering rules.

## Repo layout
- `backend/`            FastAPI service
- `frontend/`           React app (added in Step 8)
- `docker-compose.yml`  Postgres + backend (EC2 / local Docker)

## Run with Docker (Postgres + backend)
1. Fill the env files (secrets are NOT committed):
   - `cp .env.example .env`                 # Postgres creds
   - `cp backend/.env.example backend/.env` # app config (DB_*, AWS, Bedrock)
   - keep `DB_*` in `backend/.env` matching `POSTGRES_*` in `.env`
2. `docker compose up -d`
3. Open http://localhost:8000/health and http://localhost:8000/docs

## Run backend alone (dev, needs a reachable Postgres)
1. `cd backend`
2. `python -m venv .venv` and activate it
3. `pip install -r requirements.txt`
4. set `DB_HOST=localhost` in `backend/.env` (if Postgres is on the host)
5. `uvicorn app.main:app --reload`

## API (so far)
- `GET  /health`
- `POST /api/comparisons` — multipart form with `sanction_file` and `uc_file`
  (PDF/PNG/JPEG, max 20 MB each). Creates the comparison, stores both originals
  in S3 under `comparisons/<id>/<sanction|uc>/<file name>`, and returns the
  `comparison_id`, status and the two stored documents.

## Tests
```
cd backend
python -m pip install -r requirements.txt
python -m pytest            # run as `python -m pytest` so `app` is importable
```
Tests use in-memory SQLite and a stubbed S3 — no AWS calls, no database needed.

## Build roadmap (MVP-1)
1. [x] Scaffold + engineering doc + config
2. [x] Postgres models
3. [x] S3 storage + upload endpoint
4. [x] Text extraction (Textract + digital)
5. [x] LLM field extraction (Bedrock)
6. [x] Confirm endpoint + comparison math
7. [x] LLM summary + versioning
8. [x] React frontend (upload -> review -> result)
9. [ ] End-to-end test on sample pairs
