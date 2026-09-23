"""Upload + fetch endpoints for a comparison."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import Date, cast
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import (
    Comparison,
    ComparisonExtraction,
    ComparisonResult,
    ComparisonSummary,
    Document,
    DocumentContent,
)
from app.schemas import (
    ComparisonDetail,
    ComparisonListItem,
    ComparisonResultOut,
    DocumentOut,
    ExtractionOut,
    SummaryOut,
)
from app.services import extraction_pipeline, storage

router = APIRouter(prefix="/api/comparisons", tags=["comparisons"])

_ALLOWED_TYPES = {"application/pdf"}


def _store_document(
    session: Session,
    comparison_id: uuid.UUID,
    document_type: str,
    upload: UploadFile,
) -> tuple[Document, bytes]:
    """Validate, upload one file to S3, add its Document row; return it + bytes."""
    if upload.content_type not in _ALLOWED_TYPES:
        raise HTTPException(400, f"{document_type} file must be a PDF")
    data = upload.file.read()
    key = storage.build_key(comparison_id, document_type, upload.filename)
    storage.upload_bytes(key, data, upload.content_type)
    document = Document(
        comparison_id=comparison_id,
        document_type=document_type,
        file_name=upload.filename,
        s3_key=key,
        mime_type=upload.content_type,
        file_size=len(data),
        status="UPLOADED",
    )
    session.add(document)
    return document, data


def _document_out(document: Document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        document_type=document.document_type,
        file_name=document.file_name,
        s3_key=document.s3_key,
        view_url=storage.presigned_url(document.s3_key),
    )


def _detail(comparison, documents, extraction, result=None, summary=None) -> ComparisonDetail:
    return ComparisonDetail(
        comparison_id=comparison.id,
        status=comparison.status,
        documents=[_document_out(d) for d in documents],
        extraction=ExtractionOut.model_validate(extraction) if extraction else None,
        result=ComparisonResultOut.model_validate(result) if result else None,
        summary=SummaryOut.model_validate(summary) if summary else None,
    )


@router.post("", response_model=ComparisonDetail, status_code=201)
def create_comparison(
    sanction_file: UploadFile = File(...),
    expenditure_file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ComparisonDetail:
    """Store both documents, extract text + the 3 fields, return them for review."""
    comparison = Comparison(status="CREATED")
    session.add(comparison)
    session.flush()
    sanction = _store_document(session, comparison.id, "SANCTION", sanction_file)
    uc = _store_document(session, comparison.id, "UC", expenditure_file)
    comparison.status = "PROCESSING"
    session.flush()
    extraction = extraction_pipeline.run_extraction(session, comparison, [sanction, uc])
    session.commit()
    return _detail(comparison, [sanction[0], uc[0]], extraction)


@router.get("", response_model=list[ComparisonListItem])
def list_comparisons(
    q: str = "",
    date_from: date | None = None,
    date_to: date | None = None,
    session: Session = Depends(get_session),
) -> list[ComparisonListItem]:
    """History list: newest first, optionally filtered by file name and date."""
    query = session.query(Comparison).order_by(Comparison.created_at.desc())
    if date_from:
        query = query.filter(cast(Comparison.created_at, Date) >= date_from)
    if date_to:
        query = query.filter(cast(Comparison.created_at, Date) <= date_to)

    needle = q.strip().lower()
    items: list[ComparisonListItem] = []
    for comparison in query.all():
        docs = session.query(Document).filter_by(comparison_id=comparison.id).all()
        sanction = next((d.file_name for d in docs if d.document_type == "SANCTION"), "")
        uc = next((d.file_name for d in docs if d.document_type == "UC"), "")
        if needle and needle not in sanction.lower() and needle not in uc.lower():
            continue
        result = session.query(ComparisonResult).filter_by(comparison_id=comparison.id).first()
        items.append(
            ComparisonListItem(
                comparison_id=comparison.id,
                status=comparison.status,
                created_at=comparison.created_at,
                sanction_file_name=sanction,
                uc_file_name=uc,
                overall_status=result.overall_status if result else None,
                utilization_percentage=result.utilization_percentage if result else None,
            )
        )
    return items


@router.get("/{comparison_id}", response_model=ComparisonDetail)
def get_comparison(
    comparison_id: uuid.UUID, session: Session = Depends(get_session)
) -> ComparisonDetail:
    comparison = session.get(Comparison, comparison_id)
    if comparison is None:
        raise HTTPException(404, "comparison not found")
    documents = session.query(Document).filter_by(comparison_id=comparison_id).all()
    extraction = (
        session.query(ComparisonExtraction).filter_by(comparison_id=comparison_id).first()
    )
    result = session.query(ComparisonResult).filter_by(comparison_id=comparison_id).first()
    summary = (
        session.query(ComparisonSummary)
        .filter_by(comparison_id=comparison_id, is_current=True)
        .first()
    )
    return _detail(comparison, documents, extraction, result, summary)


@router.delete("/{comparison_id}", status_code=204)
def delete_comparison(
    comparison_id: uuid.UUID, session: Session = Depends(get_session)
) -> None:
    """Delete a comparison and everything tied to it (DB rows + S3 originals).

    Irreversible — used by the "Delete" action on the history list.
    """
    comparison = session.get(Comparison, comparison_id)
    if comparison is None:
        raise HTTPException(404, "comparison not found")

    documents = session.query(Document).filter_by(comparison_id=comparison_id).all()
    for document in documents:
        storage.delete_object(document.s3_key)

    session.query(ComparisonSummary).filter_by(comparison_id=comparison_id).delete()
    session.query(ComparisonResult).filter_by(comparison_id=comparison_id).delete()
    session.query(ComparisonExtraction).filter_by(comparison_id=comparison_id).delete()
    session.query(DocumentContent).filter_by(comparison_id=comparison_id).delete()
    session.query(Document).filter_by(comparison_id=comparison_id).delete()
    session.delete(comparison)
    session.commit()
