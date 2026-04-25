"""Hash chain (Huella) determinism tests.

The exact byte sequence used as input to SHA-256 is critical for chain
validation against AEAT. These tests pin the encoding so any future
refactor that breaks the hash will fail loudly.

Canonical reference: AEAT spec
``Veri-Factu_especificaciones_huella_hash_registros.pdf`` and the
EduardoRuizM/verifactu-api-python ``fingerprint()`` function (MIT).
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.modules.verifactu.services import hash_chain

MADRID = ZoneInfo("Europe/Madrid")


def _expected(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest().upper()


def test_alta_first_record_matches_canonical_string():
    nif = "B12345678"
    fecha = date(2026, 5, 2)
    dt = datetime(2026, 5, 2, 8, 49, 41, tzinfo=MADRID)

    canonical = (
        f"IDEmisorFactura={nif}"
        f"&NumSerieFactura=FAC-2026-0001"
        f"&FechaExpedicionFactura=02-05-2026"
        f"&TipoFactura=F1"
        f"&CuotaTotal=21.00"
        f"&ImporteTotal=121.00"
        f"&Huella="
        f"&FechaHoraHusoGenRegistro={dt.isoformat(timespec='seconds')}"
    )
    expected = _expected(canonical)

    got = hash_chain.fingerprint_alta(
        nif_emisor=nif,
        num_serie="FAC-2026-0001",
        fecha_expedicion=fecha,
        tipo_factura="F1",
        cuota_total=Decimal("21.00"),
        importe_total=Decimal("121.00"),
        huella_anterior="",
        fecha_hora_huso_gen_registro=dt,
    )
    assert got == expected
    assert len(got) == 64
    assert got == got.upper()


def test_alta_chained_record_uses_previous_huella():
    """Chained records embed the previous record's huella verbatim."""

    prev = "A" * 64
    nif = "B12345678"
    fecha = date(2026, 5, 2)
    dt = datetime(2026, 5, 2, 9, 0, 0, tzinfo=MADRID)

    h_first = hash_chain.fingerprint_alta(
        nif_emisor=nif,
        num_serie="X",
        fecha_expedicion=fecha,
        tipo_factura="F1",
        cuota_total=Decimal("0.00"),
        importe_total=Decimal("100.00"),
        huella_anterior="",
        fecha_hora_huso_gen_registro=dt,
    )
    h_with_prev = hash_chain.fingerprint_alta(
        nif_emisor=nif,
        num_serie="X",
        fecha_expedicion=fecha,
        tipo_factura="F1",
        cuota_total=Decimal("0.00"),
        importe_total=Decimal("100.00"),
        huella_anterior=prev,
        fecha_hora_huso_gen_registro=dt,
    )
    assert h_first != h_with_prev


def test_alta_normalises_nif_uppercase_strip():
    fecha = date(2026, 5, 2)
    dt = datetime(2026, 5, 2, 12, 0, 0, tzinfo=MADRID)

    a = hash_chain.fingerprint_alta(
        nif_emisor=" b12345678 ",
        num_serie="X",
        fecha_expedicion=fecha,
        tipo_factura="F1",
        cuota_total=Decimal("0"),
        importe_total=Decimal("100"),
        huella_anterior="",
        fecha_hora_huso_gen_registro=dt,
    )
    b = hash_chain.fingerprint_alta(
        nif_emisor="B12345678",
        num_serie="X",
        fecha_expedicion=fecha,
        tipo_factura="F1",
        cuota_total=Decimal("0"),
        importe_total=Decimal("100"),
        huella_anterior="",
        fecha_hora_huso_gen_registro=dt,
    )
    assert a == b


def test_alta_amount_format_is_two_decimals():
    """Subtle: Decimal('1') and Decimal('1.0') must hash identically."""

    fecha = date(2026, 5, 2)
    dt = datetime(2026, 5, 2, 12, 0, 0, tzinfo=MADRID)
    common = dict(
        nif_emisor="B12345678",
        num_serie="X",
        fecha_expedicion=fecha,
        tipo_factura="F1",
        huella_anterior="",
        fecha_hora_huso_gen_registro=dt,
    )

    a = hash_chain.fingerprint_alta(
        cuota_total=Decimal("1"), importe_total=Decimal("1"), **common
    )
    b = hash_chain.fingerprint_alta(
        cuota_total=Decimal("1.00"), importe_total=Decimal("1.00"), **common
    )
    c = hash_chain.fingerprint_alta(
        cuota_total=Decimal("1.0"), importe_total=Decimal("1.0"), **common
    )
    assert a == b == c


def test_anulacion_uses_anulada_field_names():
    nif = "B12345678"
    fecha = date(2026, 5, 2)
    dt = datetime(2026, 5, 2, 8, 49, 41, tzinfo=MADRID)

    canonical = (
        f"IDEmisorFacturaAnulada={nif}"
        f"&NumSerieFacturaAnulada=FAC-2026-0001"
        f"&FechaExpedicionFacturaAnulada=02-05-2026"
        f"&Huella="
        f"&FechaHoraHusoGenRegistro={dt.isoformat(timespec='seconds')}"
    )
    expected = _expected(canonical)

    got = hash_chain.fingerprint_anulacion(
        nif_emisor=nif,
        num_serie="FAC-2026-0001",
        fecha_expedicion=fecha,
        huella_anterior="",
        fecha_hora_huso_gen_registro=dt,
    )
    assert got == expected


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        hash_chain.fingerprint_alta(
            nif_emisor="B12345678",
            num_serie="X",
            fecha_expedicion=date(2026, 5, 2),
            tipo_factura="F1",
            cuota_total=Decimal("0"),
            importe_total=Decimal("100"),
            huella_anterior="",
            fecha_hora_huso_gen_registro=datetime(2026, 5, 2, 12, 0, 0),
        )
