"""API request/response schemas."""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_type: str
    file_name: str
    s3_key: str
    view_url: str = ""


class ExtractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sanctioned_amount: Decimal | None
    sanctioned_snippet: str
    expenditure_amount: Decimal | None
    expenditure_snippet: str
    expenditure_type: str
    type_snippet: str
    remarks_snippet: str = ""
    uc_purpose_snippet: str = ""
    mismatch_note: str = ""
    consistency_note: str = ""


class ComparisonResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sanction_total: Decimal
    expenditure_total: Decimal
    difference: Decimal
    utilization_percentage: Decimal
    overall_status: str
    expenditure_type: str


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int
    summary_text: str
    is_current: bool
    model_name: str
    prompt_version: str
    created_at: datetime


class ComparisonDetail(BaseModel):
    comparison_id: uuid.UUID
    status: str
    documents: list[DocumentOut]
    extraction: ExtractionOut | None = None
    result: ComparisonResultOut | None = None
    summary: SummaryOut | None = None


class ConfirmRequest(BaseModel):
    """Amounts the user reviewed/corrected on the review screen."""

    sanctioned_amount: Decimal
    expenditure_amount: Decimal
    expenditure_type: str = ""


class ConfirmResponse(BaseModel):
    result: ComparisonResultOut
    summary: SummaryOut


class ComparisonListItem(BaseModel):
    """One row in the comparison history list."""

    model_config = ConfigDict(from_attributes=True)

    comparison_id: uuid.UUID
    status: str
    created_at: datetime
    sanction_file_name: str = ""
    uc_file_name: str = ""
    overall_status: str | None = None
    utilization_percentage: Decimal | None = None
