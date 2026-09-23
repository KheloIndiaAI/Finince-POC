"""Confirm the reviewed amounts, compute the result, and manage summaries."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Comparison, ComparisonResult, ComparisonSummary
from app.schemas import (
    ComparisonResultOut,
    ConfirmRequest,
    ConfirmResponse,
    SummaryOut,
)
from app.services import comparison as comparison_math
from app.services import summary_pipeline

router = APIRouter(prefix="/api/comparisons", tags=["results"])


def _require(session: Session, comparison_id: uuid.UUID) -> Comparison:
    comparison = session.get(Comparison, comparison_id)
    if comparison is None:
        raise HTTPException(404, "comparison not found")
    return comparison


@router.post("/{comparison_id}/confirm", response_model=ConfirmResponse)
def confirm_comparison(
    comparison_id: uuid.UUID,
    body: ConfirmRequest,
    session: Session = Depends(get_session),
) -> ConfirmResponse:
    """Compute the result from the reviewed amounts, then write summary v1."""
    _require(session, comparison_id)
    outcome = comparison_math.compute(body.sanctioned_amount, body.expenditure_amount)
    result = session.query(ComparisonResult).filter_by(comparison_id=comparison_id).first()
    if result is None:
        result = ComparisonResult(comparison_id=comparison_id)
        session.add(result)
    result.sanction_total = outcome.sanction_total
    result.expenditure_total = outcome.expenditure_total
    result.difference = outcome.difference
    result.utilization_percentage = outcome.utilization_percentage
    result.overall_status = outcome.overall_status
    result.expenditure_type = body.expenditure_type
    result.result_json = {
        "utilization_percentage": str(outcome.utilization_percentage),
        "overall_status": outcome.overall_status,
    }
    session.flush()
    summary_row = summary_pipeline.create_version(session, comparison_id)
    session.commit()
    return ConfirmResponse(
        result=ComparisonResultOut.model_validate(result),
        summary=SummaryOut.model_validate(summary_row),
    )


@router.post("/{comparison_id}/summary/regenerate", response_model=SummaryOut)
def regenerate_summary(
    comparison_id: uuid.UUID, session: Session = Depends(get_session)
) -> SummaryOut:
    _require(session, comparison_id)
    summary_row = summary_pipeline.create_version(session, comparison_id)
    session.commit()
    return SummaryOut.model_validate(summary_row)


@router.get("/{comparison_id}/summaries", response_model=list[SummaryOut])
def list_summaries(
    comparison_id: uuid.UUID, session: Session = Depends(get_session)
) -> list[SummaryOut]:
    rows = (
        session.query(ComparisonSummary)
        .filter_by(comparison_id=comparison_id)
        .order_by(ComparisonSummary.version.desc())
        .all()
    )
    return [SummaryOut.model_validate(r) for r in rows]
