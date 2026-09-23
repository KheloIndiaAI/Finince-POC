"""Run the extract phase for a comparison: text -> 3 fields -> stored, EXTRACTED."""
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Comparison, ComparisonExtraction, Document, DocumentContent
from app.services import field_extraction, text_extraction


def run_extraction(
    session: Session, comparison: Comparison, docs: list[tuple[Document, bytes]]
) -> ComparisonExtraction:
    texts: dict[str, str] = {}
    for document, data in docs:
        text, method = text_extraction.extract_text(
            data, settings.s3_bucket, document.s3_key
        )
        session.add(
            DocumentContent(
                document_id=document.id,
                comparison_id=comparison.id,
                extracted_text=text,
                extraction_method=method,
            )
        )
        texts[document.document_type] = text

    fields = field_extraction.extract_fields(texts["SANCTION"], texts["UC"])
    extraction = ComparisonExtraction(
        comparison_id=comparison.id,
        sanctioned_amount=fields.sanctioned_amount,
        sanctioned_snippet=fields.sanctioned_snippet,
        expenditure_amount=fields.expenditure_amount,
        expenditure_snippet=fields.expenditure_snippet,
        expenditure_type=fields.expenditure_type,
        type_snippet=fields.type_snippet,
        remarks_snippet=fields.remarks_snippet,
        uc_purpose_snippet=fields.uc_purpose_snippet,
        mismatch_note=fields.mismatch_note,
        model_name=settings.claude_model,
        prompt_version=field_extraction.PROMPT_VERSION,
    )
    session.add(extraction)
    comparison.status = "EXTRACTED"
    session.flush()
    return extraction
