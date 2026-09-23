"""field_extraction parses the LLM JSON and normalises amounts (LLM stubbed)."""
from decimal import Decimal

from app.services import field_extraction, llm


def test_extract_fields_parses_json(monkeypatch):
    fake = (
        '{"sanctioned_amount":"67,35,600","sanctioned_snippet":"a",'
        '"expenditure_amount":2442365,"expenditure_snippet":"b",'
        '"expenditure_type":"non-recurring grant","type_snippet":"c",'
        '"uc_purpose_snippet":"Sports Equipment: Rowing",'
        '"remarks_snippet":"Rs. 1214033 to be released by SAI HO New Delhi"}'
    )
    monkeypatch.setattr(llm, "invoke", lambda prompt, **k: fake)
    fields = field_extraction.extract_fields("sanction text", "uc text")
    assert fields.sanctioned_amount == Decimal("6735600")
    assert fields.expenditure_amount == Decimal("2442365")
    assert fields.expenditure_type == "non-recurring grant"
    assert fields.uc_purpose_snippet == "Sports Equipment: Rowing"
    assert fields.remarks_snippet == "Rs. 1214033 to be released by SAI HO New Delhi"


def test_to_decimal_handles_symbols():
    assert field_extraction._to_decimal("Rs. 24,42,365/-") == Decimal("2442365")
    assert field_extraction._to_decimal(None) is None


def test_to_decimal_keeps_indian_grouping_and_paise():
    """The dot in "Rs." must not become a decimal point."""
    assert field_extraction._to_decimal("Rs.5,00,000") == Decimal("500000")
    assert field_extraction._to_decimal("Rs. 1,00,000.50/-") == Decimal("100000.50")
    assert field_extraction._to_decimal("67,35,600") == Decimal("6735600")
    assert field_extraction._to_decimal(2442365) == Decimal("2442365")
    assert field_extraction._to_decimal("") is None
    assert field_extraction._to_decimal("not an amount") is None


def test_mismatch_note_is_parsed(monkeypatch):
    """A UC from another state/year must still yield its amount, plus a warning."""
    fake = (
        '{"sanctioned_amount":"31,96,732","sanctioned_snippet":"a",'
        '"expenditure_amount":"72,29,033","expenditure_snippet":"b",'
        '"expenditure_type":"non recurring grant","type_snippet":"c",'
        '"uc_purpose_snippet":"","remarks_snippet":"",'
        '"mismatch_note":"Sanction is for Uttarakhand FY 2024-25; the UC is from '
        'the Govt. of Tripura for FY 2023-24."}'
    )
    monkeypatch.setattr(llm, "invoke", lambda prompt, **k: fake)
    fields = field_extraction.extract_fields("sanction text", "uc text")
    assert fields.expenditure_amount == Decimal("7229033")
    assert "Tripura" in fields.mismatch_note


def test_mismatch_note_defaults_to_blank(monkeypatch):
    fake = (
        '{"sanctioned_amount":1,"sanctioned_snippet":"a","expenditure_amount":1,'
        '"expenditure_snippet":"b","expenditure_type":"t","type_snippet":"c"}'
    )
    monkeypatch.setattr(llm, "invoke", lambda prompt, **k: fake)
    assert field_extraction.extract_fields("s", "u").mismatch_note == ""


def test_consistency_note_is_separate_from_mismatch(monkeypatch):
    """A differing reference number is a note to reconcile, not a mismatch."""
    fake = (
        '{"sanctioned_amount":"60,15,000","sanctioned_snippet":"a",'
        '"expenditure_amount":"72,29,033","expenditure_snippet":"b",'
        '"expenditure_type":"manpower salary","type_snippet":"c",'
        '"uc_purpose_snippet":"","remarks_snippet":"","mismatch_note":"",'
        '"consistency_note":"UC cites SLKIC/97/2023 dated 17.10.2023; the order '
        'is dated 16/10/2023 and the UC covers Q1-Q4 while the sanction covers Q1-Q3."}'
    )
    monkeypatch.setattr(llm, "invoke", lambda prompt, **k: fake)
    fields = field_extraction.extract_fields("sanction text", "uc text")
    assert fields.mismatch_note == ""
    assert "Q1-Q4" in fields.consistency_note
    assert fields.expenditure_amount == Decimal("7229033")
