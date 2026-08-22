"""Pure unit tests for compute_gst_breakdown / compute_fy_document_number.

No DB — these exercise the Decimal-safe tax-split algorithm directly.
"""

from datetime import date
from decimal import Decimal

from app.modules.india_gst.service import (
    GstLineInput,
    compute_fy_document_number,
    compute_gst_breakdown,
)


def _line(vat_rate, line_tax, invoice_item_id=None):
    return GstLineInput(invoice_item_id=invoice_item_id, vat_rate=vat_rate, line_tax=line_tax)


def test_intra_state_split_reconciles_exactly_18_percent():
    breakdown = compute_gst_breakdown(
        [_line(Decimal("18"), Decimal("1800.00"))],
        clinic_state="33",
        place_of_supply="33",
    )
    assert breakdown.is_intra is True
    line = breakdown.lines[0]
    assert line.tax_type == "intra"
    assert line.cgst_rate == Decimal("9")
    assert line.sgst_rate == Decimal("9")
    assert line.cgst_amount + line.sgst_amount == Decimal("1800.00")
    assert line.cgst_amount == Decimal("900.00")
    assert line.sgst_amount == Decimal("900.00")


def test_intra_state_halves_are_equal_even_on_odd_paise():
    """CGST and SGST are the same rate on the same value — the two heads
    must be EQUAL (GSTR-1 reconciliation rejects asymmetric heads). Each
    half rounds HALF_UP per head; the ±1 paisa drift vs line_tax on an
    odd-paise line is the expected consequence of head-wise rounding.
    """
    breakdown = compute_gst_breakdown(
        [_line(Decimal("12"), Decimal("100.01"))],
        clinic_state="27",
        place_of_supply="27",
    )
    line = breakdown.lines[0]
    assert line.cgst_amount == line.sgst_amount == Decimal("50.01")


def test_inter_state_uses_full_rate_as_igst():
    breakdown = compute_gst_breakdown(
        [_line(Decimal("18"), Decimal("1800.00"))],
        clinic_state="33",
        place_of_supply="29",
    )
    assert breakdown.is_intra is False
    line = breakdown.lines[0]
    assert line.tax_type == "inter"
    assert line.igst_rate == Decimal("18")
    assert line.igst_amount == Decimal("1800.00")
    assert line.cgst_amount == Decimal("0")
    assert line.sgst_amount == Decimal("0")


def test_rates_are_derived_per_line_not_hardcoded():
    """A 5% line and a 12% line in the same invoice must each split
    at their own rate, not a fixed 18%/9%+9%."""
    breakdown = compute_gst_breakdown(
        [_line(Decimal("5"), Decimal("50.00")), _line(Decimal("12"), Decimal("120.00"))],
        clinic_state="33",
        place_of_supply="33",
    )
    five_pct, twelve_pct = breakdown.lines
    assert five_pct.cgst_rate == Decimal("2.5")
    assert twelve_pct.cgst_rate == Decimal("6")


def test_zero_rate_line_produces_zero_tax_no_error():
    breakdown = compute_gst_breakdown(
        [_line(Decimal("0"), Decimal("0.00"))], clinic_state="33", place_of_supply="33"
    )
    line = breakdown.lines[0]
    assert line.cgst_amount == Decimal("0.00")
    assert line.sgst_amount == Decimal("0.00")


def test_negative_credit_note_amounts_split_without_re_negation():
    """Credit-note line_tax is already negative by the time it reaches
    this function (billing negates unit_price once) — the split must
    not flip the sign again."""
    breakdown = compute_gst_breakdown(
        [_line(Decimal("18"), Decimal("-1800.00"))],
        clinic_state="33",
        place_of_supply="33",
    )
    line = breakdown.lines[0]
    assert line.cgst_amount + line.sgst_amount == Decimal("-1800.00")
    assert line.cgst_amount == Decimal("-900.00")
    assert line.sgst_amount == Decimal("-900.00")


def test_missing_place_of_supply_is_not_intra():
    breakdown = compute_gst_breakdown(
        [_line(Decimal("18"), Decimal("1800.00"))],
        clinic_state="33",
        place_of_supply=None,
    )
    assert breakdown.is_intra is False


def test_multi_line_totals_sum_across_lines():
    breakdown = compute_gst_breakdown(
        [_line(Decimal("18"), Decimal("900.00")), _line(Decimal("18"), Decimal("900.00"))],
        clinic_state="33",
        place_of_supply="29",
    )
    assert breakdown.igst_total == Decimal("1800.00")
    assert breakdown.cgst_total == Decimal("0")
    assert breakdown.sgst_total == Decimal("0")


def test_fy_document_number_march_boundary():
    assert compute_fy_document_number("GST", 7, date(2026, 3, 31)) == "GST/FY25-26/0007"


def test_fy_document_number_april_boundary():
    assert compute_fy_document_number("GST", 7, date(2026, 4, 1)) == "GST/FY26-27/0007"


def test_fy_document_number_pads_sequential_number():
    assert compute_fy_document_number("CN", 1, date(2026, 8, 19)) == "CN/FY26-27/0001"
