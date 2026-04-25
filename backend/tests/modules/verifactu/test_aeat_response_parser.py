"""Parsing of AEAT responses into AeatResponse dataclass."""

from __future__ import annotations

from app.modules.verifactu.services.aeat_client import parse_response


_RESPONSE_OK = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:resp="https://example/resp">
  <soapenv:Body>
    <resp:RespuestaRegFactuSistemaFacturacion>
      <CSV>ABCDEF1234567890</CSV>
      <TimestampPresentacion>2026-05-02T08:49:41+02:00</TimestampPresentacion>
      <TiempoEsperaEnvio>60</TiempoEsperaEnvio>
      <EstadoEnvio>Correcto</EstadoEnvio>
      <RespuestaLinea>
        <IDFactura>
          <IDEmisorFactura>B12345678</IDEmisorFactura>
          <NumSerieFactura>FAC-2026-0001</NumSerieFactura>
          <FechaExpedicionFactura>02-05-2026</FechaExpedicionFactura>
        </IDFactura>
        <Operacion>Alta</Operacion>
        <EstadoRegistro>Correcto</EstadoRegistro>
      </RespuestaLinea>
    </resp:RespuestaRegFactuSistemaFacturacion>
  </soapenv:Body>
</soapenv:Envelope>"""


_RESPONSE_REJECT = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <RespuestaRegFactuSistemaFacturacion>
      <TimestampPresentacion>2026-05-02T08:49:41+02:00</TimestampPresentacion>
      <TiempoEsperaEnvio>60</TiempoEsperaEnvio>
      <EstadoEnvio>Incorrecto</EstadoEnvio>
      <RespuestaLinea>
        <IDFactura>
          <NumSerieFactura>FAC-2026-0002</NumSerieFactura>
        </IDFactura>
        <EstadoRegistro>Incorrecto</EstadoRegistro>
        <CodigoErrorRegistro>1123</CodigoErrorRegistro>
        <DescripcionErrorRegistro>NIF destinatario no válido</DescripcionErrorRegistro>
      </RespuestaLinea>
    </RespuestaRegFactuSistemaFacturacion>
  </soapenv:Body>
</soapenv:Envelope>"""


def test_parse_correcto_response():
    r = parse_response(_RESPONSE_OK)
    assert r.csv == "ABCDEF1234567890"
    assert r.estado_envio == "Correcto"
    assert r.tiempo_espera_envio == 60
    assert r.timestamp_presentacion is not None
    assert len(r.lineas) == 1
    line = r.lineas[0]
    assert line.estado_registro == "Correcto"
    assert line.id_factura["NumSerieFactura"] == "FAC-2026-0001"


def test_parse_rejection_captures_error_code_and_description():
    r = parse_response(_RESPONSE_REJECT)
    assert r.estado_envio == "Incorrecto"
    assert r.lineas[0].codigo_error == 1123
    assert "NIF destinatario" in r.lineas[0].descripcion_error
