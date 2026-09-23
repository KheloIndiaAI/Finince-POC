"""POST + GET /api/comparisons using the shared conftest fixtures.

The `client` and `uploaded` fixtures (conftest.py) give a SQLite-backed app with
S3 stubbed; here we also stub OCR and the LLM so no AWS is touched.
"""
import io
from decimal import Decimal

from app.services import field_extraction, text_extraction
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


def test_create_returns_extracted_fields(client, uploaded, monkeypatch):
    _stub_pipeline(monkeypatch)
    response = client.post("/api/comparisons", files=_pdfs())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "EXTRACTED"
    assert body["extraction"]["expenditure_type"] == "non-recurring grant"
    assert {d["document_type"] for d in body["documents"]} == {"SANCTION", "UC"}
    assert len(uploaded) == 2

    got = client.get(f"/api/comparisons/{body['comparison_id']}")
    assert got.status_code == 200
    assert Decimal(str(got.json()["extraction"]["sanctioned_amount"])) == Decimal("6735600")


def test_rejects_non_pdf(client, uploaded, monkeypatch):
    _stub_pipeline(monkeypatch)
    files = {
        "sanction_file": ("s.txt", io.BytesIO(b"x"), "text/plain"),
        "expenditure_file": ("u.pdf", io.BytesIO(b"%PDF"), "application/pdf"),
    }
    assert client.post("/api/comparisons", files=files).status_code == 400
