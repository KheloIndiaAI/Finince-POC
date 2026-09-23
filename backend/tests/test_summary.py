"""Summary versioning: new version each time, only one current, status COMPLETED."""
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    Comparison,
    ComparisonExtraction,
    ComparisonResult,
    ComparisonSummary,
)
from app.services import summary, summary_pipeline


def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _seed(session, remarks_snippet="", uc_purpose_snippet="", mismatch_note="",
          consistency_note=""):
    comparison = Comparison(status="COMPARING")
    session.add(comparison)
    session.flush()
    session.add(
        ComparisonResult(
            comparison_id=comparison.id,
            sanction_total=Decimal("100"),
            expenditure_total=Decimal("40"),
            difference=Decimal("60"),
            utilization_percentage=Decimal("40.00"),
            overall_status="UNDER_UTILIZED",
            expenditure_type="salary",
            result_json={},
        )
    )
    session.add(
        ComparisonExtraction(
            comparison_id=comparison.id,
            sanctioned_amount=Decimal("100"),
            expenditure_amount=Decimal("40"),
            expenditure_type="salary",
            remarks_snippet=remarks_snippet,
            uc_purpose_snippet=uc_purpose_snippet,
            mismatch_note=mismatch_note,
            consistency_note=consistency_note,
        )
    )
    session.flush()
    return comparison


def test_versions_increment_and_status_completes(monkeypatch):
    monkeypatch.setattr(summary, "write_summary", lambda *a, **k: "SUMMARY")
    session = _session()
    comparison = _seed(session)

    v1 = summary_pipeline.create_version(session, comparison.id)
    v2 = summary_pipeline.create_version(session, comparison.id)

    assert (v1.version, v2.version) == (1, 2)
    assert v2.is_current is True
    currents = (
        session.query(ComparisonSummary)
        .filter_by(comparison_id=comparison.id, is_current=True)
        .all()
    )
    assert len(currents) == 1
    assert session.get(Comparison, comparison.id).status == "COMPLETED"


def test_remarks_and_uc_purpose_reach_write_summary(monkeypatch):
    """Both the balance remark and the actual spending category must flow through."""
    seen = {}

    def fake_write_summary(result, remarks_snippet="", uc_purpose_snippet="",
                           mismatch_note="", consistency_note=""):
        seen["remarks"] = remarks_snippet
        seen["uc_purpose"] = uc_purpose_snippet
        return "SUMMARY"

    monkeypatch.setattr(summary, "write_summary", fake_write_summary)
    session = _session()
    comparison = _seed(
        session,
        remarks_snippet="Rs. 1214033 to be released by SAI HO New Delhi",
        uc_purpose_snippet="Sports Equipment: Rowing",
    )

    summary_pipeline.create_version(session, comparison.id)

    assert seen["remarks"] == "Rs. 1214033 to be released by SAI HO New Delhi"
    assert seen["uc_purpose"] == "Sports Equipment: Rowing"


def test_mismatch_note_reaches_write_summary(monkeypatch):
    """The warning must be handed to the summary prompt, not dropped."""
    seen = {}

    def fake_write_summary(result, remarks_snippet="", uc_purpose_snippet="",
                           mismatch_note="", consistency_note=""):
        seen["mismatch"] = mismatch_note
        return "SUMMARY"

    monkeypatch.setattr(summary, "write_summary", fake_write_summary)
    session = _session()
    comparison = _seed(session, mismatch_note="different state and year")

    summary_pipeline.create_version(session, comparison.id)

    assert seen["mismatch"] == "different state and year"


def test_consistency_note_reaches_write_summary(monkeypatch):
    """Paperwork differences travel separately from a real mismatch."""
    seen = {}

    def fake_write_summary(result, remarks_snippet="", uc_purpose_snippet="",
                           mismatch_note="", consistency_note=""):
        seen["mismatch"] = mismatch_note
        seen["consistency"] = consistency_note
        return "SUMMARY"

    monkeypatch.setattr(summary, "write_summary", fake_write_summary)
    session = _session()
    comparison = _seed(session, consistency_note="sanction letter dated a day later")

    summary_pipeline.create_version(session, comparison.id)

    assert seen["consistency"] == "sanction letter dated a day later"
    assert seen["mismatch"] == ""      # a date difference is not a mismatch
