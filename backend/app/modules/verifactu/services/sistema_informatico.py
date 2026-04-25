"""Build the ``SistemaInformatico`` block — the SIF producer identity.

The producer is the entity legally responsible for the software under
the RRSIF (Real Decreto 1007/2023). For DentalPin this varies by
deployment:

* SaaS hosted by Dentared S.L. → Dentared is the producer.
* Self-hosted by a clinic with their own IT (autodesarrollo) → the
  clinic itself is the producer.
* Self-hosted via integrator/partner → the integrator is the producer.

The producer info is stored per-clinic in ``verifactu_settings``
because in the autodesarrollo case different clinics could in theory
have different producers (rare, but allowed). Env vars provide
defaults shown by the wizard on first activation.

The clinic NIF (``ObligadoEmision``) is unrelated and goes in the SOAP
envelope cabecera.
"""

from __future__ import annotations

import os

from ..models import VerifactuSettings
from .xml_builder import SistemaInformatico


def producer_defaults() -> dict[str, str]:
    """Read producer defaults from env vars (used to prefill the wizard)."""

    return {
        "name": os.environ.get("VERIFACTU_VENDOR_NAME", ""),
        "nif": os.environ.get("VERIFACTU_VENDOR_NIF", ""),
        "id_sistema": os.environ.get("VERIFACTU_SOFTWARE_ID", "DP"),
        "version": os.environ.get("VERIFACTU_SOFTWARE_VERSION", "0.1.0"),
    }


def from_settings(settings: VerifactuSettings) -> SistemaInformatico:
    """Build a SistemaInformatico from per-clinic settings.

    Per-clinic values take precedence; if a field is blank, fall back
    to the corresponding env var.

    Field semantics (from RD 1007/2023 + AEAT spec):

    * ``TipoUsoPosibleSoloVerifactu`` — ``S`` if the SIF is hard-coded
      to operate exclusively in Veri\\*Factu mode (no XAdES journal).
      DentalPin's verifactu module only implements Veri*Factu, so ``S``.
    * ``TipoUsoPosibleMultiOT`` — ``S`` if the SIF *can* serve multiple
      obligados tributarios from one deployment. DentalPin SaaS does
      (one backend, many clinics), so ``S``.
    * ``IndicadorMultiplesOT`` — declares whether *this concrete
      installation* is currently serving multiple OTs. We instantiate a
      ``VerifactuSettings`` row per clinic and the hook only operates
      on the row matching the invoice's ``clinic_id`` — i.e. each row
      represents a single OT. Hard-coding ``S`` here triggered an AEAT
      pre-prod validator glitch, so we declare ``N`` (single OT).
    """

    defaults = producer_defaults()
    return SistemaInformatico(
        nombre_razon=settings.producer_name or defaults["name"] or "DentalPin",
        nif=settings.producer_nif or defaults["nif"] or "",
        nombre_sistema=os.environ.get("VERIFACTU_SOFTWARE_NAME", "DentalPin"),
        id_sistema=settings.producer_id_sistema or defaults["id_sistema"],
        version=settings.producer_version or defaults["version"],
        numero_instalacion=settings.numero_instalacion,
        tipo_uso_solo_verifactu="S",
        tipo_uso_multi_ot="S",
        indicador_multiples_ot="N",
    )
