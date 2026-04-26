"""HTTP client for the AEAT Veri*Factu SOAP service.

Authenticates via mTLS with the clinic's PFX certificate. Calls
``RegFactuSistemaFacturacion`` and parses the response into a typed
dataclass.

Endpoints:
    test: https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP
    prod: https://www1.agenciatributaria.gob.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import httpx
from lxml import etree

from .certificate import build_ssl_context

_ENDPOINTS = {
    "test": "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP",
    "prod": "https://www1.agenciatributaria.gob.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP",
}

# Namespaces seen in AEAT responses (the actual values depend on the
# versions of the XSDs imported). We match by local-name() in xpath to
# stay tolerant.
_LOCAL = "*[local-name()='{}']"


@dataclass
class LineResponse:
    id_factura: dict[str, str]
    operacion: str | None
    estado_registro: str | None
    codigo_error: int | None
    descripcion_error: str | None
    csv: str | None


@dataclass
class AeatResponse:
    csv: str | None
    timestamp_presentacion: datetime | None
    tiempo_espera_envio: int | None
    estado_envio: str | None
    lineas: list[LineResponse] = field(default_factory=list)
    raw_xml: str = ""


class AeatClientError(Exception):
    """Network/transport-level failure talking to AEAT."""


def endpoint_for(environment: str) -> str:
    if environment not in _ENDPOINTS:
        raise ValueError(f"Unknown environment {environment!r}")
    return _ENDPOINTS[environment]


async def submit(
    *,
    environment: str,
    pfx_bytes: bytes,
    pfx_password: str,
    soap_envelope: str,
    timeout: float = 30.0,
) -> AeatResponse:
    """Send a SOAP envelope to the configured AEAT environment.

    Raises :class:`AeatClientError` on transport-level failure (timeout,
    connection error, non-2xx HTTP status). Business-level
    rejections come back as ``estado_envio="Incorrecto"`` in the parsed
    response, *not* as an exception.
    """

    url = endpoint_for(environment)
    body = soap_envelope.encode("utf-8")

    with build_ssl_context(pfx_bytes, pfx_password) as ssl_ctx:
        try:
            async with httpx.AsyncClient(verify=ssl_ctx, timeout=timeout) as client:
                response = await client.post(
                    url,
                    content=body,
                    headers={
                        "Content-Type": "text/xml; charset=utf-8",
                        "SOAPAction": "",
                    },
                )
        except httpx.HTTPError as exc:
            raise AeatClientError(f"HTTP error talking to AEAT: {exc}") from exc

    if response.status_code >= 400:
        raise AeatClientError(f"AEAT returned HTTP {response.status_code}: {response.text[:500]}")

    return parse_response(response.text)


def _text(node, expr: str) -> str | None:
    found = node.xpath(f"./{_LOCAL.format(expr)}")
    if not found:
        # Try descendant search.
        found = node.xpath(f".//{_LOCAL.format(expr)}")
    if not found:
        return None
    val = found[0].text
    return val.strip() if val else None


def _int_or_none(s: str | None) -> int | None:
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def parse_response(xml_text: str) -> AeatResponse:
    """Parse a ``RespuestaRegFactuSistemaFacturacion`` SOAP body."""

    root = etree.fromstring(xml_text.encode("utf-8"))
    body_xpath = root.xpath(f".//{_LOCAL.format('RespuestaRegFactuSistemaFacturacion')}")
    body = body_xpath[0] if body_xpath else root

    csv = _text(body, "CSV")
    ts = _parse_dt(_text(body, "TimestampPresentacion"))
    espera = _int_or_none(_text(body, "TiempoEsperaEnvio"))
    estado = _text(body, "EstadoEnvio")

    lineas: list[LineResponse] = []
    for line_node in body.xpath(f".//{_LOCAL.format('RespuestaLinea')}"):
        id_factura: dict[str, str] = {}
        id_node = line_node.xpath(f"./{_LOCAL.format('IDFactura')}")
        if id_node:
            for child in id_node[0]:
                tag = etree.QName(child).localname
                if child.text:
                    id_factura[tag] = child.text.strip()

        lineas.append(
            LineResponse(
                id_factura=id_factura,
                operacion=_text(line_node, "Operacion") or _text(line_node, "TipoOperacion"),
                estado_registro=_text(line_node, "EstadoRegistro"),
                codigo_error=_int_or_none(_text(line_node, "CodigoErrorRegistro")),
                descripcion_error=_text(line_node, "DescripcionErrorRegistro"),
                csv=_text(line_node, "CSV"),
            )
        )

    return AeatResponse(
        csv=csv,
        timestamp_presentacion=ts,
        tiempo_espera_envio=espera,
        estado_envio=estado,
        lineas=lineas,
        raw_xml=xml_text,
    )
