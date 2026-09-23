"""GET /api/comparisons (history list): search by file name, filter by date."""
import io
import uuid
from datetime import timedelta
from decimal import Decimal

from app.models import Comparison
from app.services import field_extraction, summary, text_extraction
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
    # /confirm writes a summary; stub the LLM so tests never call Bedrock.
    monkeypatch.setattr(summary, "write_summary", lambda *a, **k: "SUMMARY")


def _pdfs(sanction_name="chandigarh_sanction.pdf", uc_name="chandigarh_uc.pdf"):
    return {
        "sanction_file": (sanction_name, io.BytesIO(b"%PDF-1.4 test"), "application/pdf"),
        "expenditure_file": (uc_name, io.BytesIO(b"%PDF-1.4 test"), "application/pdf"),
    }


def _confirm(client, comparison_id):
    return client.post(
        f"/api/comparisons/{comparison_id}/confirm",
        json={
            "sanctioned_amount": "6735600",
            "expenditure_amount": "2442365",
            "expenditure_type": "non-recurring grant",
        },
    )


def _age_by_a_minute(session_factory, comparison_id):
    """SQLite's CURRENT_TIMESTAMP only has second resolution, so rows created in the
    same second tie on created_at. Push the older row back to pin the expected order.
    """
    with session_factory() as session:
        row = session.get(Comparison, uuid.UUID(comparison_id))
        row.created_at = row.created_at - timedelta(minutes=1)
        session.commit()


def test_list_returns_newest_first_with_result_summary(
    client, uploaded, monkeypatch, session_factory
):
    _stub_pipeline(monkeypatch)
    first = client.post("/api/comparisons", files=_pdfs("a_sanction.pdf", "a_uc.pdf")).json()
    _age_by_a_minute(session_factory, first["comparison_id"])
    second = client.post("/api/comparisons", files=_pdfs("b_sanction.pdf", "b_uc.pdf")).json()
    _confirm(client, second["comparison_id"])  # only the second one has a result

    body = client.get("/api/comparisons").json()
    assert [row["comparison_id"] for row in body] == [
        second["comparison_id"],
        first["comparison_id"],
    ]
    assert body[0]["overall_status"] == "UNDER_UTILIZED"
    assert body[1]["overall_status"] is None


def test_list_filters_by_file_name(client, uploaded, monkeypatch):
    _stub_pipeline(monkeypatch)
    client.post("/api/comparisons", files=_pdfs("chandigarh_sanction.pdf", "chandigarh_uc.pdf"))
    client.post("/api/comparisons", files=_pdfs("tripura_sanction.pdf", "tripura_uc.pdf"))

    body = client.get("/api/comparisons", params={"q": "chandigarh"}).json()
    assert len(body) == 1
    assert body[0]["sanction_file_name"] == "chandigarh_sanction.pdf"
