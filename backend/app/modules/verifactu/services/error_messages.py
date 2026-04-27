"""User-friendly Spanish translations of common AEAT Veri\\*Factu errors.

The AEAT response includes a ``CodigoErrorRegistro`` integer plus a
``DescripcionErrorRegistro`` string, but the official descriptions
are written for tax-administration auditors and read poorly in our
queue UI ("Error en el bloque de SistemaInformatico…"). This module
turns the most common codes into actionable Spanish messages aimed
at clinic administrators, AND tags each message with the affected
``field`` and a ``suggested_cta`` so the frontend can show a targeted
"fix it here" button instead of dropping the user into an error wall.

Coverage: codes documented in ``docs/modules/verifactu.md`` §8 plus
the most-frequent entries from the official catalogue
``Validaciones_Errores_Veri-Factu.pdf``. Unmapped codes fall back to
the raw AEAT description with ``field=None`` and ``cta="contact_support"``.

Sentinel codes (added by ``services.submission_queue``):

* ``-1`` — transport error (TLS/HTTP) before AEAT could respond.
* ``-2`` — SOAP Fault returned by AEAT (no per-record reply lines).
"""

from __future__ import annotations

from typing import Literal, TypedDict

ErrorField = Literal[
    "emisor",
    "destinatario",
    "linea",
    "cabecera",
    "cadena",
    "transporte",
    "sistema",
    "rectificativa",
]
ErrorCTA = Literal[
    "edit_clinic",
    "edit_billing_party",
    "edit_lines",
    "edit_producer",
    "retry",
    "contact_support",
]


class FriendlyError(TypedDict):
    """Tagged version of an AEAT error suitable for the UI."""

    message: str
    field: ErrorField | None
    suggested_cta: ErrorCTA | None


# (message, field, cta)
_ENTRIES: dict[int, tuple[str, ErrorField | None, ErrorCTA | None]] = {
    # ---------- Sentinels ----------------------------------------------
    -1: (
        "Error de transporte al contactar con la AEAT (TLS o HTTP). "
        "El envío se reintentará automáticamente.",
        "transporte",
        "retry",
    ),
    -2: (
        "La AEAT devolvió un SOAP Fault sin detalle por registro. "
        "Suele indicar incidencia temporal del servicio. Reintento automático.",
        "transporte",
        "retry",
    ),
    # ---------- AEAT-side infrastructure -------------------------------
    103: (
        "Incidencia interna en los servidores de la AEAT (Codigo[103]). "
        "No es un error del envío; reintentaremos automáticamente.",
        "transporte",
        "retry",
    ),
    -904: (
        "Recurso de la AEAT no disponible (Codigo[-904]). "
        "Incidencia temporal del servicio; reintento automático.",
        "transporte",
        "retry",
    ),
    # ---------- Esquema XML / SistemaInformatico ----------------------
    1100: (
        "El identificador del sistema informático (IdSistemaInformatico) "
        "es incorrecto. Debe tener exactamente 2 caracteres alfanuméricos. "
        "Revísalo en Productor del SIF.",
        "sistema",
        "edit_producer",
    ),
    1103: (
        "El campo ID es incorrecto. Suele indicar NIF mal formado, fecha "
        "no DD-MM-AAAA o número de factura vacío.",
        "cabecera",
        "edit_clinic",
    ),
    # ---------- Cabecera / NIF EMISOR (4101..4116) --------------------
    4101: (
        "Falta o es inválido el bloque Cabecera del envío. "
        "Generalmente indica un fallo interno del módulo; contacta soporte.",
        "cabecera",
        "contact_support",
    ),
    4102: (
        "El XML no cumple el esquema (falta algún campo obligatorio en "
        "Cabecera). Suele resolverse con la última versión del módulo.",
        "cabecera",
        "contact_support",
    ),
    4116: (
        "El NIF de la clínica (ObligadoEmision) tiene un formato incorrecto. "
        "Revisa el CIF/NIF en Configuración → Clínica (debe tener "
        "9 caracteres y dígito de control válido).",
        "emisor",
        "edit_clinic",
    ),
    # ---------- IDFactura / receptor (4117..4140) ---------------------
    4117: (
        "El NIF del destinatario tiene formato incorrecto. Edita los datos "
        "fiscales del cliente en la factura.",
        "destinatario",
        "edit_billing_party",
    ),
    4128: (
        "El bloque IDFactura es inválido (NIF emisor, fecha o serie). "
        "Verifica que la clínica tiene NIF y razón social correctos.",
        "emisor",
        "edit_clinic",
    ),
    4140: (
        "Datos del destinatario incompletos o inválidos para una factura "
        "completa (F1). Edita los datos fiscales del cliente.",
        "destinatario",
        "edit_billing_party",
    ),
    4153: (
        "El bloque Desglose es inválido. Revisa la clasificación AEAT "
        "(S1/E1/N1) en Mapeo de IVA y los importes de la factura.",
        "linea",
        "edit_lines",
    ),
    # ---------- SistemaInformatico (NIF productor) --------------------
    4109: (
        "El NIF del productor del SIF tiene un dígito de control "
        "incorrecto. Corrígelo en Productor del SIF (debe ser un CIF/NIF "
        "real con dígito de control válido).",
        "sistema",
        "edit_producer",
    ),
    # ---------- Calificación de operación -----------------------------
    1237: (
        "Se ha indicado una operación no sujeta (N1/N2) con tipo "
        "impositivo o cuota. Revisa el mapeo AEAT del tipo de IVA: para "
        "0% sin sujeción no se puede informar TipoImpositivo ni "
        "CuotaRepercutida.",
        "linea",
        "edit_lines",
    ),
    # ---------- Rectificativas ----------------------------------------
    1142: (
        "La factura rectificativa (R1/R2/...) no referencia correctamente "
        "la factura original. Verifica que la factura origen existe y "
        "está en estado 'aceptada' por la AEAT.",
        "rectificativa",
        "contact_support",
    ),
    # ---------- Cadena / huella ---------------------------------------
    3000: (
        "La AEAT detectó un salto en la cadena de huellas. Suele ocurrir "
        "tras importar registros manualmente o tras un fallo de envío "
        "previo no resuelto. Contacta soporte antes de reintentar.",
        "cadena",
        "contact_support",
    ),
}


def friendly_message(codigo: int | None, fallback: str | None = None) -> str | None:
    """Return a Spanish UX message for an AEAT error code.

    Kept for backward compatibility — new callers should prefer
    :func:`friendly_error` to also receive the ``field`` and
    ``suggested_cta`` tags.
    """

    if codigo is None:
        return fallback
    entry = _ENTRIES.get(codigo)
    if entry is None:
        return fallback
    return entry[0]


def friendly_error(
    codigo: int | None,
    fallback: str | None = None,
) -> FriendlyError:
    """Return tagged friendly error for an AEAT code.

    The ``field`` and ``suggested_cta`` keys let the UI render a
    targeted "Fix this in <X>" button instead of a wall of text.
    """

    if codigo is None:
        return FriendlyError(
            message=fallback or "Sin información de error.",
            field=None,
            suggested_cta=None,
        )
    entry = _ENTRIES.get(codigo)
    if entry is None:
        return FriendlyError(
            message=fallback or f"Error AEAT (código {codigo}).",
            field=None,
            suggested_cta="contact_support",
        )
    message, field, cta = entry
    return FriendlyError(message=message, field=field, suggested_cta=cta)
