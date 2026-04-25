"""SHA-256 hash chain (``Huella``) per AEAT Veri*Factu specification.

Algorithm and field order are taken from the AEAT spec PDF
``Veri-Factu_especificaciones_huella_hash_registros.pdf`` and the
reference open-source implementation
https://github.com/EduardoRuizM/verifactu-api-python (MIT) — function
``fingerprint()`` in ``app/verifactu.py`` lines 76-86. Original code is
MIT-licensed; we use that field order and algorithm here. The wrapper,
typing, and integration are ours.

The chain is global per ``obligado tributario`` (clinic NIF). The
"previous record" is whichever ``VerifactuRecord`` was most recently
accepted by AEAT for that NIF, regardless of whether it was an alta or
an anulacion. The very first record carries an empty previous huella
and ``<PrimerRegistro>S</PrimerRegistro>``.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from decimal import Decimal


def _normalize_nif(nif: str) -> str:
    return nif.strip().upper()


def _format_amount(amount: Decimal) -> str:
    return f"{amount:.2f}"


def _format_fecha_expedicion(fecha: date) -> str:
    return f"{fecha:%d-%m-%Y}"


def _format_fecha_hora_huso(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("fecha_hora_huso must be timezone-aware (Madrid/Canarias).")
    return dt.isoformat(timespec="seconds")


def fingerprint_alta(
    *,
    nif_emisor: str,
    num_serie: str,
    fecha_expedicion: date,
    tipo_factura: str,
    cuota_total: Decimal,
    importe_total: Decimal,
    huella_anterior: str,
    fecha_hora_huso_gen_registro: datetime,
) -> str:
    """Build the ``Huella`` for a ``RegistroAlta``.

    See the AEAT spec for the exact key=value order — it is **not** an
    arbitrary ampersand-join: changing the order or the formatting
    breaks chain validation.
    """

    canonical = (
        f"IDEmisorFactura={_normalize_nif(nif_emisor)}"
        f"&NumSerieFactura={num_serie}"
        f"&FechaExpedicionFactura={_format_fecha_expedicion(fecha_expedicion)}"
        f"&TipoFactura={tipo_factura}"
        f"&CuotaTotal={_format_amount(cuota_total)}"
        f"&ImporteTotal={_format_amount(importe_total)}"
        f"&Huella={huella_anterior}"
        f"&FechaHoraHusoGenRegistro={_format_fecha_hora_huso(fecha_hora_huso_gen_registro)}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


def fingerprint_anulacion(
    *,
    nif_emisor: str,
    num_serie: str,
    fecha_expedicion: date,
    huella_anterior: str,
    fecha_hora_huso_gen_registro: datetime,
) -> str:
    """Build the ``Huella`` for a ``RegistroAnulacion``.

    Field names switch to the ``...Anulada`` variant per AEAT spec.
    """

    canonical = (
        f"IDEmisorFacturaAnulada={_normalize_nif(nif_emisor)}"
        f"&NumSerieFacturaAnulada={num_serie}"
        f"&FechaExpedicionFacturaAnulada={_format_fecha_expedicion(fecha_expedicion)}"
        f"&Huella={huella_anterior}"
        f"&FechaHoraHusoGenRegistro={_format_fecha_hora_huso(fecha_hora_huso_gen_registro)}"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()
