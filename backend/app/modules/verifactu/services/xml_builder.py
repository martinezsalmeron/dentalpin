"""Build SOAP envelopes for AEAT Veri*Factu submissions.

Two layers:

* :func:`render_registro_alta` / :func:`render_registro_anulacion` build
  a single ``<RegistroFactura>`` body from a payload dataclass.
* :func:`render_envelope` wraps N already-rendered registros in the SOAP
  envelope with the ``<Cabecera>`` block.

We use Jinja2 with autoescape enabled, then optionally validate the
result against the AEAT XSD before sending. XSD validation is a
defence-in-depth layer; the templates are conservative and use
``| e``/``| safe`` carefully so XML escaping happens uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(enabled_extensions=("xml", "j2"), default=False),
    keep_trailing_newline=False,
    trim_blocks=True,
    lstrip_blocks=True,
)


@dataclass(frozen=True)
class SistemaInformatico:
    nombre_razon: str
    nif: str
    nombre_sistema: str = "DentalPin"
    id_sistema: str = "DP"
    version: str = "0.1.0"
    numero_instalacion: str = ""
    tipo_uso_solo_verifactu: str = "S"
    tipo_uso_multi_ot: str = "S"
    indicador_multiples_ot: str = "S"

    def to_dict(self) -> dict:
        return {
            "nombre_razon": self.nombre_razon,
            "nif": self.nif,
            "nombre_sistema": self.nombre_sistema,
            "id_sistema": self.id_sistema,
            "version": self.version,
            "numero_instalacion": self.numero_instalacion,
            "tipo_uso_solo_verifactu": self.tipo_uso_solo_verifactu,
            "tipo_uso_multi_ot": self.tipo_uso_multi_ot,
            "indicador_multiples_ot": self.indicador_multiples_ot,
        }


@dataclass
class IDFacturaRef:
    nif: str
    num_serie: str
    fecha: str  # DD-MM-YYYY


@dataclass
class DesgloseLine:
    impuesto: str
    clave_regimen: str
    base_imponible: Decimal
    calificacion_operacion: str | None = None
    operacion_exenta: bool = False
    causa_exencion: str | None = None
    tipo_impositivo: Decimal | None = None
    cuota_repercutida: Decimal | None = None


@dataclass
class Destinatario:
    nombre_razon: str
    nif: str | None = None
    id_otro: dict | None = None


@dataclass
class RegistroAltaPayload:
    nif_emisor: str
    nombre_razon_emisor: str
    serie_numero: str
    fecha_expedicion: date
    tipo_factura: str  # F1|F2|F3|R1|R2|R5
    descripcion_operacion: str
    desglose: list[DesgloseLine]
    cuota_total: Decimal
    importe_total: Decimal
    sistema_informatico: SistemaInformatico
    fecha_hora_huso_gen_registro: datetime
    huella: str
    huella_anterior: str = ""
    is_first_record: bool = False
    id_factura_anterior: IDFacturaRef | None = None
    destinatario: Destinatario | None = None
    tipo_rectificativa: str | None = None
    facturas_rectificadas: list[IDFacturaRef] = field(default_factory=list)
    importe_rectificacion: dict | None = None
    subsanacion: bool = False
    rechazo_previo: bool = False


@dataclass
class RegistroAnulacionPayload:
    nif_emisor: str
    serie_numero: str
    fecha_expedicion: date
    huella: str
    fecha_hora_huso_gen_registro: datetime
    sistema_informatico: SistemaInformatico
    huella_anterior: str = ""
    is_first_record: bool = False
    id_factura_anterior: IDFacturaRef | None = None


def _fmt_fecha(d: date) -> str:
    return f"{d:%d-%m-%Y}"


def _fmt_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("fecha_hora_huso must be timezone-aware")
    return dt.isoformat(timespec="seconds")


def render_registro_alta(payload: RegistroAltaPayload) -> str:
    tpl = _env.get_template("registro_alta.xml.j2")
    return tpl.render(
        nif_emisor=payload.nif_emisor,
        nombre_razon_emisor=payload.nombre_razon_emisor,
        serie_numero=payload.serie_numero,
        fecha_expedicion=_fmt_fecha(payload.fecha_expedicion),
        tipo_factura=payload.tipo_factura,
        tipo_rectificativa=payload.tipo_rectificativa,
        descripcion_operacion=payload.descripcion_operacion,
        destinatario=(
            {
                "nombre_razon": payload.destinatario.nombre_razon,
                "nif": payload.destinatario.nif,
                "id_otro": payload.destinatario.id_otro,
            }
            if payload.destinatario
            else None
        ),
        desglose=[
            {
                "impuesto": d.impuesto,
                "clave_regimen": d.clave_regimen,
                "base_imponible": d.base_imponible,
                "calificacion_operacion": d.calificacion_operacion,
                "operacion_exenta": d.operacion_exenta,
                "causa_exencion": d.causa_exencion,
                "tipo_impositivo": d.tipo_impositivo,
                "cuota_repercutida": d.cuota_repercutida,
            }
            for d in payload.desglose
        ],
        cuota_total=payload.cuota_total,
        importe_total=payload.importe_total,
        is_first_record=payload.is_first_record,
        huella_anterior=payload.huella_anterior,
        id_factura_anterior=(
            {
                "nif": payload.id_factura_anterior.nif,
                "num_serie": payload.id_factura_anterior.num_serie,
                "fecha": payload.id_factura_anterior.fecha,
            }
            if payload.id_factura_anterior
            else None
        ),
        sistema_informatico=payload.sistema_informatico.to_dict(),
        fecha_hora_huso=_fmt_iso(payload.fecha_hora_huso_gen_registro),
        huella=payload.huella,
        facturas_rectificadas=[
            {"nif": f.nif, "num_serie": f.num_serie, "fecha": f.fecha}
            for f in payload.facturas_rectificadas
        ]
        or None,
        importe_rectificacion=payload.importe_rectificacion,
        subsanacion=payload.subsanacion,
        rechazo_previo=payload.rechazo_previo,
    )


def render_registro_anulacion(payload: RegistroAnulacionPayload) -> str:
    tpl = _env.get_template("registro_anulacion.xml.j2")
    return tpl.render(
        nif_emisor=payload.nif_emisor,
        serie_numero=payload.serie_numero,
        fecha_expedicion=_fmt_fecha(payload.fecha_expedicion),
        huella=payload.huella,
        huella_anterior=payload.huella_anterior,
        is_first_record=payload.is_first_record,
        id_factura_anterior=(
            {
                "nif": payload.id_factura_anterior.nif,
                "num_serie": payload.id_factura_anterior.num_serie,
                "fecha": payload.id_factura_anterior.fecha,
            }
            if payload.id_factura_anterior
            else None
        ),
        sistema_informatico=payload.sistema_informatico.to_dict(),
        fecha_hora_huso=_fmt_iso(payload.fecha_hora_huso_gen_registro),
    )


def render_envelope(
    *,
    cabecera_obligado_nif: str,
    cabecera_obligado_nombre: str,
    registros_xml: list[str],
) -> str:
    tpl = _env.get_template("soap_envelope.xml.j2")
    return tpl.render(
        cabecera_obligado_nif=cabecera_obligado_nif,
        cabecera_obligado_nombre=cabecera_obligado_nombre,
        registros_xml=registros_xml,
    )
