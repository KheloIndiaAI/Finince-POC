"""DELETE /api/comparisons/{id}: removes every row tied to it, plus S3 originals."""
import io
from decimal import Decimal

from app.models import (
    Comparison,
    ComparisonExtraction,
    ComparisonResult,
    ComparisonSummary,
    Document,
)
from app.services import field_extraction, storage, text_extraction
from app.services.field_extraction import ExtractedFields

_FIELDS = ExtractedFields(
    sanctioned_amount=Decimal("6735600"),
    sanctioned_snippet="s",
    expenditure_amount=Decimal("2442365"),
    expenditure_snippet="e",
    expenditure_type="non-recurring grant",
    type_snippet="t",
)


def _stub_pipeline(monkeypatch):
    monkeypatch.setattr(text_extraction, "extract_text", lambda data, b, k: ("text", "TEXT"))
    monkeypatch.setattr(field_extraction, "extract_fields", lambda s, u: _FIELDS)


def _pdfs():
    return {
        "sanction_file": ("s.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf"),
        "expenditure_file": ("u.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf"),
    }


def test_delete_removes_every_row(client, uploaded, monkeypatch, session_factory):
    _stub_pipeline(monkeypatch)
    deleted_keys = []
    monkeypatch.setattr(storage, "delete_object", lambda key: deleted_keys.append(key))

    created = client.post("/api/comparisons", files=_pdfs()).json()
    comparison_id = created["comparison_id"]
    client.post(
        f"/api/comparisons/{comparison_id}/confirm",
        json={
            "sanctioned_amount": "6735600",
            "expenditure_amount": "2442365",
            "expenditure_type": "non-recurring grant",
        },
    )

    response = client.delete(f"/api/comparisons/{comparison_id}")
    assert response.status_code == 204
    assert len(deleted_keys) == 2  # sanction + uc originals

    assert client.get(f"/api/comparisons/{comparison_id}").status_code == 404

    session = session_factory()
    import uuid

    cid = uuid.UUID(comparison_id)
    assert session.get(Comparison, cid) is None
    assert session.query(Document).filter_by(comparison_id=cid).count() == 0
    assert session.query(ComparisonExtraction).filter_by(comparison_id=cid).count() == 0
    assert session.query(ComparisonResult).filter_by(comparison_id=cid).count() == 0
    assert session.query(ComparisonSummary).filter_by(comparison_id=cid).count() == 0


def test_delete_missing_comparison_is_404(client):
    import uuid

    response = client.delete(f"/api/comparisons/{uuid.uuid4()}")
    assert response.status_code == 404
