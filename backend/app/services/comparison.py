"""Deterministic comparison math. No LLM, no I/O — just Decimal arithmetic."""
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass
class ComparisonOutcome:
    sanction_total: Decimal
    expenditure_total: Decimal
    difference: Decimal
    utilization_percentage: Decimal
    overall_status: str


def compute(sanctioned: Decimal, expenditure: Decimal) -> ComparisonOutcome:
    difference = sanctioned - expenditure
    if sanctioned > 0:
        pct = (expenditure / sanctioned * Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        pct = Decimal("0.00")
    return ComparisonOutcome(
        sanction_total=sanctioned,
        expenditure_total=expenditure,
        difference=difference,
        utilization_percentage=pct,
        overall_status=_status(sanctioned, expenditure),
    )


def _status(sanctioned: Decimal, expenditure: Decimal) -> str:
    if expenditure == sanctioned:
        return "FULLY_UTILIZED"
    if expenditure < sanctioned:
        return "UNDER_UTILIZED"
    return "OVER_UTILIZED"
