"""Veri*Factu QR code generation.

The QR encodes a URL to AEAT's ValidarQR endpoint with four parameters:
``nif``, ``numserie``, ``fecha`` (DD-MM-YYYY), ``importe`` (2 decimals).

Test environment uses ``prewww1.aeat.es``; production uses
``www1.agenciatributaria.gob.es``. The host swap is the only difference.

Spec: ``DetalleEspecificacTecnCodigoQRfactura.pdf``. We render at ECC
level M with ``box_size=8`` and a 4-module quiet zone, which fits in
the 30-40 mm window the spec requires for A4 invoice PDFs.
"""

from __future__ import annotations

import base64
from datetime import date
from decimal import Decimal
from io import BytesIO
from urllib.parse import quote

import qrcode
from qrcode.constants import ERROR_CORRECT_M

_TEST_HOST = "prewww1.aeat.es"
_PROD_HOST = "www1.agenciatributaria.gob.es"


def _host(environment: str) -> str:
    if environment == "prod":
        return _PROD_HOST
    if environment == "test":
        return _TEST_HOST
    raise ValueError(f"Unknown environment {environment!r}")


def build_qr_url(
    *,
    environment: str,
    nif: str,
    num_serie: str,
    fecha_expedicion: date,
    importe_total: Decimal,
) -> str:
    """Return the URL to encode in the Veri*Factu QR."""

    host = _host(environment)
    params = (
        f"nif={quote(nif.strip().upper(), safe='')}"
        f"&numserie={quote(num_serie, safe='')}"
        f"&fecha={quote(f'{fecha_expedicion:%d-%m-%Y}', safe='')}"
        f"&importe={quote(f'{importe_total:.2f}', safe='')}"
    )
    return f"https://{host}/wlpl/TIKE-CONT/ValidarQR?{params}"


def render_png(url: str, *, box_size: int = 8, border: int = 4) -> bytes:
    """Render the QR as PNG bytes, ECC level M per AEAT spec."""

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def render_png_base64(url: str, **kwargs) -> str:
    """Convenience: PNG as base64 for embedding in HTML/PDF templates."""
    return base64.b64encode(render_png(url, **kwargs)).decode("ascii")
