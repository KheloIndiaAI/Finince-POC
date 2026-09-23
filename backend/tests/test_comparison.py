"""Deterministic comparison math."""
from decimal import Decimal

from app.services.comparison import compute


def test_under_utilized_matches_document():
    o = compute(Decimal("6735600"), Decimal("2442365"))
    assert o.difference == Decimal("4293235")
    assert o.utilization_percentage == Decimal("36.26")
    assert o.overall_status == "UNDER_UTILIZED"


def test_fully_and_over_utilized():
    assert compute(Decimal("100"), Decimal("100")).overall_status == "FULLY_UTILIZED"
    assert compute(Decimal("100"), Decimal("120")).overall_status == "OVER_UTILIZED"


def test_zero_sanction_is_safe():
    assert compute(Decimal("0"), Decimal("50")).utilization_percentage == Decimal("0.00")
