"""Test app wired to a throwaway SQLite database, with S3 and the LLM stubbed out."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import Base
from app.services import llm, storage


@pytest.fixture(autouse=True)
def stub_llm(monkeypatch):
    """No test may reach Bedrock. Tests that care about the wording stub
    llm.invoke or summary.write_summary themselves, which overrides this.
    """
    monkeypatch.setattr(llm, "invoke", lambda prompt, **kwargs: "Stubbed summary.")


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def uploaded(monkeypatch):
    """Record what would have gone to S3 instead of calling AWS."""
    calls = []

    def fake_upload(key: str, data: bytes, content_type: str) -> str:
        calls.append({"key": key, "size": len(data), "content_type": content_type})
        return key

    monkeypatch.setattr(storage, "upload_bytes", fake_upload)
    monkeypatch.setattr(storage, "presigned_url", lambda key, expires_in=3600: f"https://example-signed/{key}")
    monkeypatch.setattr(storage, "delete_object", lambda key: None)
    return calls


@pytest.fixture()
def client(session_factory):
    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
