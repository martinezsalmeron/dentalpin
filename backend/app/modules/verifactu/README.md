# Verifactu module — Spanish AEAT compliance

Implements the Spanish RRSIF / Veri\*Factu regime (RD 1007/2023, Orden
HAC/1177/2024, RDL 15/2025) so DentalPin clinics in Spain can comply
with the mandatory e-invoicing rules:

| Population | Mandatory date |
|---|---|
| Sociedades (corporations) | **2027-01-01** |
| Autónomos / IRPF | **2027-07-01** |

## What it does

- Hooks into the billing module via `BillingComplianceHook` — never
  imports billing internals directly.
- On every issued invoice, builds a `RegistroAlta` (or `RegistroAnulacion`)
  with SHA-256 chained hash, signs it with the clinic's FNMT certificate
  via mTLS, and submits it to AEAT's Veri\*Factu SOAP service.
- Generates the Veri\*Factu QR encoded for the AEAT validation URL.
- Maintains an append-only fiscal ledger (`verifactu_records`) — legal
  retention 4 years.
- Per-clinic config + per-clinic FNMT certificate, encrypted at rest
  (Fernet derived from `SECRET_KEY`).
- Test (`prewww1.aeat.es`) vs production (`www1.agenciatributaria.gob.es`)
  toggle. Production switch requires admin confirmation.

## Producer responsibility — important

Under RD 1007/2023 art. 13, every Sistema Informático de Facturación
(SIF) has a **producer** legally responsible for the software's
compliance. The producer must sign a *declaración responsable* and is
exposed to LGT 201 bis sanctions if the software does not comply.

DentalPin is open-source (BSL 1.1 → Apache 2.0 after 4 years). The
producer role depends on **who deploys and operates the software**:

| Deployment model | Producer (productor del SIF) |
|---|---|
| Managed SaaS at `dentalpin.com` | The SaaS operator (e.g. Dentared Odontology Services S.L.) |
| Self-hosted by a clinic with its own IT (autodesarrollo) | The clinic itself |
| Self-hosted via integrator/partner | The integrator |
| Local development, no real fiscal use | None — Veri\*Factu must stay disabled |

The DentalPin codebase **does not** designate a default producer. The
`<SistemaInformatico>` block sent to AEAT is filled per-deployment from
the wizard at `/settings/verifactu/producer` (or env vars
`VERIFACTU_VENDOR_NIF` and `VERIFACTU_VENDOR_NAME` as defaults). The
operator is responsible for:

1. Filling the producer wizard with their own NIF + razón social.
2. Signing the declaración responsable in the wizard. The signature is
   timestamped and bound to the user, providing audit evidence for
   AEAT inspections.
3. Validating end-to-end against `prewww1.aeat.es` with a real FNMT
   certificate before flipping the environment to `prod`.
4. Keeping the software up to date with regulation changes.

Until the producer wizard is filled and the declaración signed, the
backend rejects any attempt to enable Verifactu in production.

## Configuration

Per-deployment env vars (used as defaults shown by the wizard):

```bash
VERIFACTU_VENDOR_NIF=                 # Producer NIF (real CIF — leave blank if set per-clinic in wizard)
VERIFACTU_VENDOR_NAME=                # Producer legal name
VERIFACTU_SOFTWARE_NAME=DentalPin     # Optional, default DentalPin
VERIFACTU_SOFTWARE_ID=DP              # 2-char system ID
VERIFACTU_SOFTWARE_VERSION=0.1.0      # Software version string
```

Per-clinic config (stored in `verifactu_settings`):

- `enabled` (bool)
- `environment` (`test` / `prod`)
- `nif_emisor` (the clinic NIF)
- `nombre_razon_emisor` (clinic legal name)
- Producer info (NIF, name, ID, version, declaración signed timestamp)
- One active PFX certificate in `verifactu_certificates`

## Module lifecycle

- `auto_install=False` — install manually from `Admin → Modules`.
- `removable=True`, but `uninstall()` blocks if any record reached
  `accepted` state (legal retention).
- Migrations on the `verifactu` Alembic branch.

## Architecture summary

```
on invoice.issued (billing)
        │
        ▼
VerifactuHook (BillingComplianceHook)
        │  build RegistroAlta XML
        │  compute SHA-256 chained Huella
        │  insert VerifactuRecord (state="pending")
        ▼
APScheduler worker every 60s
        │  acquire pg advisory lock per clinic
        │  batch ≤1000 pending records
        │  decrypt PFX, build mTLS context
        │  POST SOAP to AEAT (test or prod)
        │  parse RespuestaRegFactuSistemaFacturacion
        ▼
update record state + Invoice.compliance_data['ES']
```

## What this module does NOT do

- Non-Veri\*Factu mode (XAdES + event journal). RRSIF allows it but is
  more work for no upside; out of scope.
- TicketBAI (País Vasco) — separate regime, separate module.
- Croquetas. Or any other regional regime.
- Auto-publishing the declaración responsable — the wizard prepares
  the PDF; you must publish/distribute it to your customers.

## References

- RD 1007/2023 (BOE-A-2023-24840)
- Orden HAC/1177/2024 (BOE-A-2024-22138)
- AEAT Veri\*Factu portal: <https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html>
- AEAT preproduction endpoint: `https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP`
- Reference open-source implementation (MIT, used as reference for
  hash + XML templates): <https://github.com/EduardoRuizM/verifactu-api-python>
