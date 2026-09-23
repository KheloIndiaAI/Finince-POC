"""Local dev entrypoint: `python run.py` starts the API on http://localhost:8000.

Equivalent to `uvicorn app.main:app --reload`, just runnable without
remembering the module path. Requires backend/.env to be filled in
(AWS keys, DB_HOST=localhost when Postgres runs via `docker compose up postgres`).
"""
import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    # boto3 reads AWS credentials from the process environment, which Docker fills
    # from env_file; do the same here for the host-run path. Real environment
    # variables take precedence, so `DB_PORT=55433 python run.py` still works.
    load_dotenv()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
