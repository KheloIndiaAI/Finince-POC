from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import comparisons, results
from app.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Sanction vs UC Comparison", lifespan=lifespan)

# Dev CORS: allow the React dev server. Tighten before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(comparisons.router)
app.include_router(results.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "region": settings.aws_region}
