"""SQLAlchemy models. Every row ties back to one comparison via comparison_id.

Column types are dialect-agnostic (Uuid, Numeric, JSON) so the same models run
on Postgres in production and on SQLite in tests.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def _id() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class Comparison(Base, TimestampMixin):
    __tablename__ = "comparisons"
    id: Mapped[uuid.UUID] = _id()
    status: Mapped[str] = mapped_column(String(32), default="CREATED")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = _id()
    comparison_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comparisons.id"))
    document_type: Mapped[str] = mapped_column(String(16))  # SANCTION | UC
    file_name: Mapped[str] = mapped_column(String(255))
    s3_key: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(128), default="")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADED")


class DocumentContent(Base, TimestampMixin):
    __tablename__ = "document_content"
    id: Mapped[uuid.UUID] = _id()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"))
    comparison_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comparisons.id"))
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    extraction_method: Mapped[str] = mapped_column(String(32), default="")  # TEXT | TEXTRACT


class ComparisonExtraction(Base, TimestampMixin):
    __tablename__ = "comparison_extractions"
    id: Mapped[uuid.UUID] = _id()
    comparison_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comparisons.id"))
    sanctioned_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    sanctioned_snippet: Mapped[str] = mapped_column(Text, default="")
    expenditure_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    expenditure_snippet: Mapped[str] = mapped_column(Text, default="")
    expenditure_type: Mapped[str] = mapped_column(String(255), default="")
    type_snippet: Mapped[str] = mapped_column(Text, default="")
    remarks_snippet: Mapped[str] = mapped_column(Text, default="")
    uc_purpose_snippet: Mapped[str] = mapped_column(Text, default="")
    mismatch_note: Mapped[str] = mapped_column(Text, default="")
    model_name: Mapped[str] = mapped_column(String(128), default="")
    prompt_version: Mapped[str] = mapped_column(String(32), default="")


class ComparisonResult(Base, TimestampMixin):
    __tablename__ = "comparison_results"
    id: Mapped[uuid.UUID] = _id()
    comparison_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comparisons.id"))
    sanction_total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    expenditure_total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    difference: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    utilization_percentage: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    overall_status: Mapped[str] = mapped_column(String(32))
    expenditure_type: Mapped[str] = mapped_column(String(255), default="")
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ComparisonSummary(Base, TimestampMixin):
    __tablename__ = "comparison_summaries"
    id: Mapped[uuid.UUID] = _id()
    comparison_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("comparisons.id"))
    version: Mapped[int] = mapped_column(Integer)
    summary_text: Mapped[str] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(128), default="")
    prompt_version: Mapped[str] = mapped_column(String(32), default="")
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
