"""Schema smoke test: all tables build on a throwaway SQLite database."""
from sqlalchemy import create_engine, inspect

from app.models import Base

EXPECTED = {
    "comparisons",
    "documents",
    "document_content",
    "comparison_extractions",
    "comparison_results",
    "comparison_summaries",
}


def test_all_tables_create():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    assert set(inspect(engine).get_table_names()) == EXPECTED
