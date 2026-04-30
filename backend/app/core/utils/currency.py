"""Locale-aware currency formatting.

Single helper used by every server-rendered surface (PDFs, emails,
report exports) so the format is consistent and never reinvents
symbols, separators, or decimal places. Wraps ``babel.numbers`` —
the standard for ICU-quality formatting in Python.
"""

from decimal import Decimal

from babel.numbers import format_currency as _babel_format_currency


def format_currency(
    amount: Decimal | float | int,
    currency: str,
    locale: str = "es_ES",
) -> str:
    """Render ``amount`` as a localized currency string.

    ``locale`` accepts both BCP 47 (``en-US``) and POSIX (``en_US``);
    babel only accepts the latter, so we normalize.
    """
    return _babel_format_currency(amount, currency, locale=locale.replace("-", "_"))
