"""Spanish NIF / NIE / CIF mod-23 validator."""

from __future__ import annotations

import pytest

from app.modules.verifactu.services.nif_validator import (
    is_valid_spanish_nif,
    nif_warning,
)


@pytest.mark.parametrize(
    "value",
    [
        "12345678Z",  # canonical DNI from AEAT examples
        "00000000T",
        "X1234567L",  # NIE
        "Y0000000Z",
        "B98765431",  # CIF empresa S.L. (digit control)
        "A58818501",  # CIF empresa S.A. (digit control)
    ],
)
def test_is_valid_spanish_nif_valid(value: str) -> None:
    assert is_valid_spanish_nif(value)


@pytest.mark.parametrize(
    "value",
    [
        "B12345678",  # demo seed: real format but bad CIF check digit
        "12345678A",  # DNI wrong letter
        "X1234567A",  # NIE wrong letter
        "ZZZZZZZZZ",
        "",
        None,
        "abc",
        "12345678",  # too short / no letter
    ],
)
def test_is_valid_spanish_nif_invalid(value: str | None) -> None:
    assert not is_valid_spanish_nif(value)


def test_nif_warning_returns_message_for_invalid() -> None:
    assert nif_warning("B12345678") is not None


def test_nif_warning_silent_for_valid() -> None:
    assert nif_warning("12345678Z") is None


def test_nif_warning_silent_for_empty() -> None:
    # Absence of NIF is the caller's concern, not a format problem.
    assert nif_warning("") is None
    assert nif_warning(None) is None
