"""Turn the computed result into plain sentences via the LLM.

The numbers and the verdict are decided by Python; the LLM only phrases them.
"""
from app.services import llm
from app.services.prompts import load_prompt

_PROMPT_NAME = "summary_v5.md"
PROMPT_VERSION = "summary_v5"


def write_summary(
    result,
    remarks_snippet: str = "",
    uc_purpose_snippet: str = "",
    mismatch_note: str = "",
    consistency_note: str = "",
) -> str:
    prompt = (
        load_prompt(_PROMPT_NAME)
        .replace("[[SANCTIONED]]", str(result.sanction_total))
        .replace("[[EXPENDITURE]]", str(result.expenditure_total))
        .replace("[[DIFFERENCE]]", str(result.difference))
        .replace("[[UTILIZATION]]", str(result.utilization_percentage))
        .replace("[[STATUS]]", result.overall_status)
        .replace("[[TYPE]]", result.expenditure_type or "the sanctioned purpose")
        .replace("[[UC_PURPOSE]]", uc_purpose_snippet or "")
        .replace("[[REMARKS]]", remarks_snippet or "")
        .replace("[[MISMATCH]]", mismatch_note or "")
        .replace("[[CONSISTENCY]]", consistency_note or "")
    )
    return llm.invoke(prompt, max_tokens=400).strip()
