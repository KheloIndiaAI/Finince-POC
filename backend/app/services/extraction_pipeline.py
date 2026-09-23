"""Run the extract phase for a comparison: text -> 3 fields -> stored, EXTRACTED."""
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Comparison, ComparisonExtraction, Document, DocumentContent
from app.services import field_extraction, text_extraction


def run_extraction(
    session: Session, comparison: Comparison, docs: list[tuple[Document, bytes]]
) -> ComparisonExtraction:
    # Both documents are OCR'd at once: each Textract job spends most of its
    # time queued, so running them in sequence doubles the wait for no reason.
    with ThreadPoolExecutor(max_workers=len(docs)) as pool:
        results = list(
            pool.map(
                lambda pair: text_extraction.extract_text(
                    pair[1], settings.s3_bucket, pair[0].s3_key
                ),
                docs,
            )
        )

    texts: dict[str, str] = {}
    for (document, _), (text, method) in zip(docs, results):
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
        consistency_note=fields.consistency_note,
        model_name=settings.claude_model,
        prompt_version=field_extraction.PROMPT_VERSION,
    )
    session.add(extraction)
    comparison.status = "EXTRACTED"
    session.flush()
    return extraction
