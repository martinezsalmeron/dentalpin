"""Spanish NIF / NIE / CIF validator (mod-23 + CIF check digit).

Used to surface a *warning* — not a hard block — when a clinic enters
an obviously malformed NIF. AEAT's error 4116 (and friends) reject the
register at submission time, so catching the typo at entry / before
issue saves a round-trip.

Rules implemented:

* **DNI** — 8 digits + control letter (TRWAGMYFPDXBNJZSQVHLCKE table).
* **NIE** — leading X/Y/Z + 7 digits + control letter (X→0, Y→1, Z→2).
* **CIF** — leading letter (A-W subset) + 7 digits + control digit
  (modulus algorithm; final char is digit or letter depending on the
  organisation type).

Returns booleans + a friendly message; never raises. Callers decide
whether to block or just warn.
"""

from __future__ import annotations

import re
import string

_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_DNI_RE = re.compile(r"^\d{8}[A-Z]$")
_NIE_RE = re.compile(r"^[XYZ]\d{7}[A-Z]$")
_CIF_RE = re.compile(r"^[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]$")
_CIF_LETTER_TABLE = "JABCDEFGHI"
# Organisation types that REQUIRE a letter as control digit, not a digit.
_CIF_LETTER_ONLY = "PQSNW"
# Types that REQUIRE a digit as control digit.
_CIF_DIGIT_ONLY = "ABEH"


def _normalize(value: str) -> str:
    return value.strip().upper().replace(" ", "").replace("-", "")


def _check_dni(value: str) -> bool:
    if not _DNI_RE.match(value):
        return False
    number = int(value[:8])
    expected = _DNI_LETTERS[number % 23]
    return value[8] == expected


def _check_nie(value: str) -> bool:
    if not _NIE_RE.match(value):
        return False
    prefix_map = {"X": "0", "Y": "1", "Z": "2"}
    digits = prefix_map[value[0]] + value[1:8]
    number = int(digits)
    expected = _DNI_LETTERS[number % 23]
    return value[8] == expected


def _check_cif(value: str) -> bool:
    if not _CIF_RE.match(value):
        return False
    org_type = value[0]
    digits = value[1:8]
    given_control = value[8]

    odd_sum = 0
    even_sum = 0
    for idx, ch in enumerate(digits):
        d = int(ch)
        if idx % 2 == 0:  # positions 1,3,5,7 (1-indexed) → even index here
            doubled = d * 2
            odd_sum += (doubled // 10) + (doubled % 10)
        else:
            even_sum += d

    total = odd_sum + even_sum
    expected_digit = (10 - (total % 10)) % 10
    expected_letter = _CIF_LETTER_TABLE[expected_digit]

    if org_type in _CIF_LETTER_ONLY:
        return given_control == expected_letter
    if org_type in _CIF_DIGIT_ONLY:
        return given_control == str(expected_digit)
    return given_control == str(expected_digit) or given_control == expected_letter


def is_valid_spanish_nif(value: str | None) -> bool:
    """True if ``value`` parses as a valid Spanish DNI / NIE / CIF.

    Empty / None returns False (callers decide whether absence is OK).
    """

    if not value:
        return False
    v = _normalize(value)
    if not v:
        return False
    if v[0] in string.digits:
        return _check_dni(v)
    if v[0] in "XYZ":
        return _check_nie(v)
    return _check_cif(v)


def nif_warning(value: str | None) -> str | None:
    """Return a Spanish warning message when ``value`` is not a valid NIF.

    Returns ``None`` when the value parses cleanly. Callers should treat
    the return as advisory (UI hint), not as an exception.
    """

    if not value:
        return None
    if is_valid_spanish_nif(value):
        return None
    return (
        "El formato del NIF/CIF no parece válido. AEAT puede rechazar la "
        "factura. Revisa que tenga 9 caracteres y dígito de control correcto."
    )
