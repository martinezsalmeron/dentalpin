"""XML builder smoke tests — well-formedness + key element presence."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from lxml import etree

from app.modules.verifactu.services import xml_builder

MADRID = ZoneInfo("Europe/Madrid")


def _well_formed(s: str) -> etree._Element:
    # Wrap the registro fragment in a synthetic root with the namespace
    # used by the surrounding envelope so xpath checks work.
    wrapper = (
        '<root xmlns:sum="https://www2.agenciatributaria.gob.es/static_files/'
        'common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd">'
        f"{s}"
        "</root>"
    )
    return etree.fromstring(wrapper.encode("utf-8"))


def _make_payload(*, tipo_factura: str = "F1", with_destinatario: bool = True):
    si = xml_builder.SistemaInformatico(
        nombre_razon="DentalPin S.L.",
        nif="B00000000",
        numero_instalacion="abc-123",
    )
    desglose = [
        xml_builder.DesgloseLine(
            impuesto="01",
            clave_regimen="01",
            base_imponible=Decimal("100.00"),
            calificacion_operacion="S1",
            tipo_impositivo=Decimal("21"),
            cuota_repercutida=Decimal("21.00"),
        ),
    ]
    destinatario = (
        xml_builder.Destinatario(nombre_razon="Juan García", nif="12345678Z")
        if with_destinatario
        else None
    )
    return xml_builder.RegistroAltaPayload(
        nif_emisor="B12345678",
        nombre_razon_emisor="Clínica Dental de Prueba",
        serie_numero="FAC-2026-0001",
        fecha_expedicion=date(2026, 5, 2),
        tipo_factura=tipo_factura,
        descripcion_operacion="Servicios odontológicos",
        desglose=desglose,
        cuota_total=Decimal("21.00"),
        importe_total=Decimal("121.00"),
        sistema_informatico=si,
        fecha_hora_huso_gen_registro=datetime(2026, 5, 2, 12, 0, 0, tzinfo=MADRID),
        huella="A" * 64,
        is_first_record=True,
        destinatario=destinatario,
    )


def test_alta_f1_includes_destinatario_with_nif():
    xml_str = xml_builder.render_registro_alta(_make_payload(tipo_factura="F1"))
    root = _well_formed(xml_str)
    nif = root.xpath(".//*[local-name()='IDDestinatario']/*[local-name()='NIF']/text()")
    assert nif == ["12345678Z"]


def test_alta_f2_uses_factura_sin_identif():
    xml_str = xml_builder.render_registro_alta(
        _make_payload(tipo_factura="F2", with_destinatario=False)
    )
    root = _well_formed(xml_str)
    flag = root.xpath(".//*[local-name()='FacturaSinIdentifDestinatarioArt61d']/text()")
    assert flag == ["S"]


def test_alta_first_record_has_primer_registro_s():
    xml_str = xml_builder.render_registro_alta(_make_payload())
    root = _well_formed(xml_str)
    flag = root.xpath(".//*[local-name()='PrimerRegistro']/text()")
    assert flag == ["S"]


def test_alta_includes_sistema_informatico():
    xml_str = xml_builder.render_registro_alta(_make_payload())
    root = _well_formed(xml_str)
    assert root.xpath(
        ".//*[local-name()='SistemaInformatico']/*[local-name()='NombreSistemaInformatico']/text()"
    ) == ["DentalPin"]
    assert root.xpath(
        ".//*[local-name()='SistemaInformatico']/*[local-name()='NumeroInstalacion']/text()"
    ) == ["abc-123"]


def test_amounts_formatted_two_decimals():
    xml_str = xml_builder.render_registro_alta(_make_payload())
    assert "<CuotaTotal>21.00</CuotaTotal>" in xml_str
    assert "<ImporteTotal>121.00</ImporteTotal>" in xml_str


def test_envelope_wraps_n_records():
    xml_str_a = xml_builder.render_registro_alta(_make_payload())
    xml_str_b = xml_builder.render_registro_alta(_make_payload())
    envelope = xml_builder.render_envelope(
        cabecera_obligado_nif="B12345678",
        cabecera_obligado_nombre="Clínica Dental",
        registros_xml=[xml_str_a, xml_str_b],
    )
    root = etree.fromstring(envelope.encode("utf-8"))
    registros = root.xpath(".//*[local-name()='RegistroFactura']")
    assert len(registros) == 2
