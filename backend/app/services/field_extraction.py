"""Ask the LLM to pick the fields from the two documents' text.

The LLM only reads values; Python converts amounts to Decimal here.
"""
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.services import llm
from app.services.prompts import load_prompt

_PROMPT_NAME = "extraction_v5.md"
PROMPT_VERSION = "extraction_v5"


@dataclass
class ExtractedFields:
    sanctioned_amount: Decimal | None
    sanctioned_snippet: str
    expenditure_amount: Decimal | None
    expenditure_snippet: str
    expenditure_type: str
    type_snippet: str
    remarks_snippet: str = ""
    uc_purpose_snippet: str = ""
    mismatch_note: str = ""


def extract_fields(sanction_text: str, uc_text: str) -> ExtractedFields:
    prompt = (
        load_prompt(_PROMPT_NAME)
        .replace("[[SANCTION_TEXT]]", sanction_text)
        .replace("[[UC_TEXT]]", uc_text)
    )
    data = _parse_json(llm.invoke(prompt))
    return ExtractedFields(
        sanctioned_amount=_to_decimal(data.get("sanctioned_amount")),
        sanctioned_snippet=str(data.get("sanctioned_snippet") or ""),
        expenditure_amount=_to_decimal(data.get("expenditure_amount")),
        expenditure_snippet=str(data.get("expenditure_snippet") or ""),
        expenditure_type=str(data.get("expenditure_type") or ""),
        type_snippet=str(data.get("type_snippet") or ""),
        remarks_snippet=str(data.get("remarks_snippet") or ""),
        uc_purpose_snippet=str(data.get("uc_purpose_snippet") or ""),
        mismatch_note=str(data.get("mismatch_note") or ""),
    )


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("LLM did not return JSON")
    return json.loads(match.group(0))


# Amounts arrive as "Rs. 24,42,365/-", "Rs.5,00,000.50" or a bare number. Match the
# first run of digits (Indian grouping included) rather than stripping non-digits,
# so the dot in "Rs." cannot be read as a decimal point.
_AMOUNT_RE = re.compile(r"\d[\d,\s]*(?:\.\d+)?")


def _to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    match = _AMOUNT_RE.search(str(value))
    if not match:
        return None
    cleaned = re.sub(r"[,\s]", "", match.group(0))
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None
