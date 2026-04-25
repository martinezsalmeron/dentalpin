"""QR URL formatting + PNG render smoke tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.modules.verifactu.services import qr


def test_url_test_environment_uses_prewww1_host():
    url = qr.build_qr_url(
        environment="test",
        nif="B12345678",
        num_serie="FAC-2026-0001",
        fecha_expedicion=date(2026, 5, 2),
        importe_total=Decimal("121.00"),
    )
    assert url.startswith("https://prewww1.aeat.es/wlpl/TIKE-CONT/ValidarQR?")
    assert "nif=B12345678" in url
    assert "numserie=FAC-2026-0001" in url
    assert "fecha=02-05-2026" in url
    assert "importe=121.00" in url


def test_url_prod_environment_uses_official_host():
    url = qr.build_qr_url(
        environment="prod",
        nif="B12345678",
        num_serie="X",
        fecha_expedicion=date(2026, 1, 1),
        importe_total=Decimal("0.00"),
    )
    assert url.startswith("https://www1.agenciatributaria.gob.es/")


def test_url_unknown_environment_raises():
    with pytest.raises(ValueError):
        qr.build_qr_url(
            environment="staging",
            nif="X",
            num_serie="Y",
            fecha_expedicion=date(2026, 1, 1),
            importe_total=Decimal("0.00"),
        )


def test_render_png_returns_non_empty_bytes_with_png_signature():
    png = qr.render_png("https://example.com/qr")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 100
