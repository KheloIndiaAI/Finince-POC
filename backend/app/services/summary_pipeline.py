"""Create a new summary version and mark it current; keep all previous versions."""
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Comparison, ComparisonExtraction, ComparisonResult, ComparisonSummary
from app.services import summary


def create_version(session: Session, comparison_id) -> ComparisonSummary:
    result = (
        session.query(ComparisonResult).filter_by(comparison_id=comparison_id).first()
    )
    if result is None:
        raise ValueError("no result to summarise")

    extraction = (
        session.query(ComparisonExtraction).filter_by(comparison_id=comparison_id).first()
    )
    remarks_snippet = extraction.remarks_snippet if extraction else ""
    uc_purpose_snippet = extraction.uc_purpose_snippet if extraction else ""
    mismatch_note = extraction.mismatch_note if extraction else ""
    consistency_note = extraction.consistency_note if extraction else ""

    text = summary.write_summary(
        result, remarks_snippet, uc_purpose_snippet, mismatch_note, consistency_note
    )
    session.query(ComparisonSummary).filter_by(
        comparison_id=comparison_id, is_current=True
    ).update({"is_current": False})

    last = (
        session.query(ComparisonSummary)
        .filter_by(comparison_id=comparison_id)
        .order_by(ComparisonSummary.version.desc())
        .first()
    )
    row = ComparisonSummary(
        comparison_id=comparison_id,
        version=(last.version + 1) if last else 1,
        summary_text=text,
        model_name=settings.claude_model,
        prompt_version=summary.PROMPT_VERSION,
        is_current=True,
    )
    session.add(row)
    session.get(Comparison, comparison_id).status = "COMPLETED"
    session.flush()
    return row
