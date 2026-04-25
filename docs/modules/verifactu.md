# Verifactu — Installation & Operation Manual

> **Optional module — Spain only.** Compliance with the Spanish RRSIF /
> Veri\*Factu regime (RD 1007/2023, Orden HAC/1177/2024). Mandatory for
> issuing invoices in Spain from 2027. Voluntary phase open since 2026
> with no penalties for technical errors.

| Population | Mandatory date |
|---|---|
| Sociedades (IS) | **2027-01-01** |
| Autónomos / IRPF / others | **2027-07-01** |
| SIF software vendors | **2025-07-29** (passed — voluntary mode is live) |

Legal sources: [RD 1007/2023 (BOE-A-2023-24840)](https://www.boe.es/buscar/act.php?id=BOE-A-2023-24840),
[Orden HAC/1177/2024](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-22138),
RDL 15/2025, RD 254/2025.

---

## Contents

1. [What this module does](#1-what-this-module-does)
2. [Architecture & module boundaries](#2-architecture--module-boundaries)
3. [Installation](#3-installation)
4. [Setup walkthrough (5 steps)](#4-setup-walkthrough-5-steps)
5. [Daily operation](#5-daily-operation)
6. [VAT classification mapping](#6-vat-classification-mapping)
7. [Test vs production environments](#7-test-vs-production-environments)
8. [AEAT validation errors — catalogue](#8-aeat-validation-errors--catalogue)
9. [Troubleshooting](#9-troubleshooting)
10. [Data model](#10-data-model)
11. [API endpoints](#11-api-endpoints)
12. [Permissions](#12-permissions)
13. [Pre-production checklist](#13-pre-production-checklist)
14. [References](#14-references)

---

## 1. What this module does

When a clinic in Spain has the module enabled and issues an invoice,
Verifactu silently:

1. Builds a `RegistroAlta` (or `RegistroAnulacion`) XML payload with
   AEAT-mandated fields, namespaces and ordering.
2. Computes the SHA-256 chained `Huella` (links each record to the
   previous one in the clinic's fiscal chain).
3. Stores the record in `verifactu_records` (state=`pending`).
4. Returns preliminary `compliance_data['ES']` to the invoice (huella,
   QR URL, tipo_factura, environment).
5. A periodic worker (every 60 s) drains pending records, signs the
   SOAP envelope with the clinic's FNMT certificate via mTLS, sends
   them to AEAT in batches up to 1 000, parses
   `RespuestaRegFactuSistemaFacturacion`, updates state + CSV +
   timestamp, and mirrors the final state back into the invoice.

Each invoice's PDF embeds a QR code with a URL to AEAT's `ValidarQR`
endpoint — anyone holding the printed invoice can verify it in real
time on AEAT.

---

## 2. Architecture & module boundaries

DentalPin is international software; AEAT/RRSIF is Spain-only. The
verifactu module is therefore optional, country-specific, and isolated.

**Module dependencies (declared in `manifest.depends`):**
- `billing` — to register the country compliance hook.
- `catalog` — to read/map `vat_types` for AEAT classification.

**What verifactu does NOT do:**
- Modify `vat_types` (catalog stays country-agnostic — only `rate` and
  `names`, no AEAT taxonomy).
- Modify `invoices`/`invoice_items` (billing stays fiscal-neutral).
- Add columns to core/billing/catalog tables. All Spain-specific data
  lives in tables prefixed `verifactu_*`.
- Lock billing flow. If verifactu is disabled, billing operates as if
  the module wasn't installed.

**How it plugs in:**
- Hook is registered via `BillingHookRegistry.register(VerifactuHook())`
  on every backend boot (in `VerifactuModule.__init__`). Routing is
  per-invoice based on `clinic.settings.country == "ES"`.
- The hook reads from its own tables (`verifactu_settings`,
  `verifactu_certificates`, `verifactu_records`,
  `verifactu_vat_classifications`) plus reads (no FK changes) from
  `clinics`, `vat_types` and `invoice_items`.

This pattern is reusable: a future `factur-x-fr` (France) or `sdi-it`
(Italy) module ships its own tables, its own classification mapping,
and its own UI under `/settings/<module>`. Each country module owns
its complexity.

---

## 3. Installation

### 3.1 Build the backend image

Verifactu adds `httpx`, `lxml`, `qrcode[pil]` and `cryptography` to the
backend dependencies. They are already declared in `pyproject.toml`,
so a fresh build picks them up:

```bash
docker-compose up -d --build backend
```

### 3.2 Run migrations

```bash
docker-compose exec backend alembic upgrade heads
```

This applies four migrations on the `verifactu` Alembic branch:
- `vfy_0001_initial` — settings, certificates, records.
- `vfy_0002_producer_info` — SIF producer fields + signature.
- `vfy_0003_drop_emisor_columns` — issuer NIF moved to `clinics`.
- `vfy_0004_vat_classifications` — per-clinic AEAT classification overrides.

### 3.3 Reconcile the module registry

The host backend reconciles all on-disk modules at startup. Restarting
is enough:

```bash
docker-compose restart backend
```

The module appears in `Admin → Modules` as `uninstalled` (because
`auto_install=False`).

### 3.4 Install from the admin UI

1. Sign in as admin.
2. Go to `Admin → Modules`.
3. Find **verifactu** in the list and click **Install**.
4. The installer:
   - Confirms migrations are at head (no-op if already applied).
   - Runs the lifecycle hook — registers `VerifactuHook` for ES, starts
     the APScheduler worker, and seeds default VAT classifications
     (`E1` for every existing zero-rate VAT type).
   - Promotes the record to `state=installed`.
5. The verifactu card appears in `Configuration` with quick links to
   the configuration sub-pages.

If the host frontend's `modules.json` has changed, restart the
frontend so the Nuxt layer re-discovers verifactu's pages:

```bash
docker-compose restart frontend
```

### 3.5 Optional environment variables

```bash
# Defaults shown by the producer wizard. Per-clinic wizard values
# always win; env vars are fallbacks for fresh installs.
VERIFACTU_VENDOR_NIF=                # Producer NIF (real CIF)
VERIFACTU_VENDOR_NAME=               # Producer legal name
VERIFACTU_SOFTWARE_NAME=DentalPin    # Optional, defaults to "DentalPin"
VERIFACTU_SOFTWARE_ID=DP             # 2-char system identifier
VERIFACTU_SOFTWARE_VERSION=0.1.0     # Pin to your deploy's version tag
```

---

## 4. Setup walkthrough (5 steps)

Once installed, every clinic that wants to emit invoices through
Verifactu must complete these steps in order. Status of each prereq
is shown as a checklist in the verifactu home (`/settings/verifactu`).

### Step 1 — Clinic identity

Verifactu reads the issuer NIF from the clinic itself, not from
verifactu settings (single source of truth, shared with all modules).

1. Go to `Configuration` → `Clinic information` → `Edit`.
2. Fill **CIF/NIF** with the clinic's real fiscal NIF.
3. (Recommended) Fill **Razón social** if the legal name differs from
   the commercial name. AEAT's `NombreRazonEmisor` falls back to the
   clinic's `name` when `legal_name` is empty.
4. Set **Country** to *España* (or any country code; the verifactu
   hook auto-sets `country=ES` when verifactu is activated, so this is
   optional).
5. Save.

### Step 2 — Digital certificate (FNMT)

Verifactu signs every SOAP submission with the clinic's certificate
via mTLS. Real production needs a real cert; preproduction accepts
AEAT-issued test certs.

1. Obtain a `.pfx` / `.p12` certificate. Valid types:
   - **Certificado de Representante de Persona Jurídica** (companies).
   - **Certificado de Persona Física** (autónomos whose NIF matches the
     clinic's `tax_id`).
   - **Sello de Empresa** (alternative for entities).
   Request from [the FNMT portal](https://www.sede.fnmt.gob.es/certificados/certificado-de-representante).
2. Go to `/settings/verifactu/certificate`.
3. Drag & drop the `.pfx` file (or click the dropzone). Format and
   size are validated client-side.
4. Enter the certificate password.
5. Click **Subir certificado**.

The file and password are encrypted with the server key (Fernet) and
stored in `verifactu_certificates`. The cert subject CN is parsed from
the bundle for display. Replacing the cert deactivates the previous
one but keeps it in history (audit trail).

A status panel at the top shows expiry: green if >60 days remain,
amber 15-60 days, red <15 days or expired.

### Step 3 — SIF producer

The "productor del SIF" is the legal entity that puts the software
into production and signs the *declaración responsable* per RD
1007/2023 art. 13.

| Deployment model | Producer is |
|---|---|
| Managed SaaS at e.g. dentalpin.com | The SaaS operator |
| Self-hosted by a clinic with own IT | The clinic (autodesarrollo) |
| Self-hosted via integrator/partner | The integrator |
| Local development | None — keep verifactu disabled |

1. Go to `/settings/verifactu/producer`. Three numbered cards.
2. **Step 1 — Datos del productor:** fill NIF, razón social, system ID
   (2 chars, default `DP`), version. Click **Guardar datos sin firmar**
   to persist a draft.
3. **Step 2 — Firmar declaración responsable:** read the inline
   declaration text (the same content as the downloadable PDF). Tick
   "He leído y acepto la declaración responsable…". Click
   **Firmar electrónicamente**. The server seals
   `declaracion_responsable_signed_at` and `_by` with your timestamp
   and user ID — sufficient evidence for an AEAT audit.
4. **Step 3 — Descargar PDF firmado:** opens a printable HTML page
   with the declaration + electronic-signature stamp. Useful as
   evidence for AEAT, internal archive, or distribution to client
   clinics if you operate as SaaS.

After signing, all producer fields are locked. The Step 1 alert shows
an **"Anular firma para editar"** button that opens a confirmation
modal: revoking clears the signature, force-disables Verifactu, and
unlocks the fields. Records already submitted to AEAT are not
affected — only future submissions reflect the new producer.

### Step 4 — VAT classification mapping (AEAT)

Each catalog VAT type must map to an AEAT classification (S1, E1, N1,
etc.). The module seeds defaults at install time.

1. Go to `/settings/verifactu/vat-mapping`.
2. For each VAT type (e.g. *General 21%*, *Reducido 10%*, *Exento 0%*),
   pick its AEAT classification:
   - **S1 — Sujeto, no exento (régimen general)** for VAT >0%.
   - **E1 — Exento (art. 20 LIVA — sanitario, financiero…)** for
     dental clinical services with rate=0% (default seeded for any
     existing 0% type).
   - **E2-E6** for export, intracomunitario, etc.
   - **N1/N2 — No sujeta (regla localización)** for non-VAT lines
     where 0% reflects no taxability rather than exemption.
   - **Auto** to fall back to the rate-based heuristic.
3. Click the per-row **Guardar**. Each row's effective classification
   is shown next to the dropdown.

> The mapping table (`verifactu_vat_classifications`) lives inside
> the verifactu module. The catalog `vat_types` table stays
> country-agnostic. Other country compliance modules can ship their
> own equivalent table without touching catalog.

### Step 5 — Activate Verifactu

1. Go to `/settings/verifactu`. The status hero will say
   *"Listo para activar"* (orange checklist becomes a green/blue ready
   panel) when steps 1-4 are complete.
2. Click **Activar Verifactu**. The hook is now live: every issued
   invoice produces a Verifactu record and queues for AEAT submission.
3. The hero turns blue: *"Verifactu activo en pruebas"*. The
   environment badge says `Pruebas` (test).

To switch to production, click **Cambiar a producción** in the same
hero. A red modal asks for confirmation:
*"Vas a pasar a producción real. Las facturas que se emitan a partir
de ahora se enviarán a la AEAT como datos fiscales reales."*

---

## 5. Daily operation

### Issuing an invoice

The flow is automatic — billing-side UX is unchanged. From the user's
perspective:

1. Create an invoice (draft). Add items. Save.
2. Click **Emitir factura**. Workflow validates billing data, runs
   the `validate_before_issue` hook (Verifactu checks: NIF emisor,
   producer signed, certificate active, F2 cap ≤400€ if no
   destinatario NIF), assigns invoice number, writes
   `compliance_data['ES']` with huella + QR URL + record_id.
3. The invoice transitions to `issued`. The Verifactu panel on the
   invoice detail page shows the QR + huella + state.
4. Within 60 s, the worker picks up the record, sends it to AEAT,
   updates `state` (Correcto / AceptadoConErrores / Incorrecto), and
   stores the AEAT CSV.

### Monitoring

Two pages:

- **`/settings/verifactu/queue`** — current submissions, three tabs:
  - *Pendientes* — `state in (pending, sending)`.
  - *Rechazados* — `state=rejected` (AEAT business rejection).
  - *Errores temporales* — `state=failed_transient` (transport issues,
    AEAT side faults). Each row shows the AEAT error code + message,
    submission attempt count, and a **Reintentar (Subsanación)**
    action that resends with `Subsanacion=S` (and `RechazoPrevio=X`
    when the previous attempt was `Incorrecto`).
- **`/settings/verifactu/records`** — immutable fiscal ledger with
  every record (any state). Filters by state and tipo_factura.

### Worker — internal flow

```
APScheduler IntervalTrigger(60 s) → process_verifactu_submissions()
        │
        ▼ for each clinic with enabled=true, in its own session:
process_clinic(db, clinic_id)
        ├─ pg_try_advisory_xact_lock(hash('verifactu:'||uuid))
        │     └─ if not acquired: skip (another worker has the clinic)
        ├─ if now < next_send_after: skip   ← TiempoEsperaEnvio
        ├─ load active certificate
        ├─ load clinic.tax_id + .legal_name|name (issuer)
        ├─ SELECT records WHERE state IN (pending, failed_transient)
        ├─ mark batch state=sending
        ├─ decrypt PFX + password (Fernet)
        ├─ build_ssl_context (tempfile 0600 + immediate unlink)
        ├─ render envelope (Cabecera + N RegistroFactura)
        ├─ httpx.AsyncClient(verify=ssl_ctx).post(endpoint, body)
        ├─ parse RespuestaRegFactuSistemaFacturacion
        ├─ for each record: match by NumSerieFactura → update state
        │     ├─ Correcto / AceptadoConErrores → mirror into
        │     │   invoice.compliance_data['ES']
        │     └─ Incorrecto → state=rejected, surface code+desc
        ├─ if response is a SOAP Fault (no lineas): copy faultstring
        │   into aeat_descripcion_error for every record (codigo=-2)
        └─ settings.next_send_after = now + tiempo_espera_envio
```

On transport-level failure (timeout, HTTP 4xx/5xx), records are
marked `failed_transient` with `aeat_codigo_error=-1` and the message
captured. The worker retries on next tick — exponential backoff via
`submission_attempt`.

---

## 6. VAT classification mapping

This is the architectural decision that keeps the module
country-isolated.

### What it solves

Catalog `vat_types` stores `rate` and a localized name. That's
enough for billing math (compute IVA per line) but not for AEAT
reporting — AEAT requires every line to declare a
`CalificacionOperacion` (S1, S2, N1, N2) or `OperacionExenta`
(E1..E6) value.

Naively encoding S1/E1/N1 in `vat_types` would force every other
country compliance module to share Spanish concepts. So verifactu
ships its own per-clinic mapping table.

### How it works

Table `verifactu_vat_classifications` (per clinic):

| Column | Purpose |
|---|---|
| `clinic_id` | Owner |
| `vat_type_id` | FK to `vat_types` (CASCADE) |
| `classification` | `S1`, `S2`, `E1`-`E6`, `N1`, `N2` |
| `exemption_cause` | `E1`-`E6` redundant copy when classification is exempt |
| `notes` | Free text (e.g. *"art. 20.uno.3.º LIVA"*) |

When the hook builds a `Desglose`, it loads
`{vat_type_id: override}` for the clinic. For each invoice item:
- If override exists → use literal classification.
- Else → fall back to `iva_classifier.classify(rate, is_exento_sanitario)`
  heuristic.

### Default seed

At install time, verifactu inserts an `E1` override for every
existing `vat_type` with `rate=0`, with the note
*"Servicios sanitarios — art. 20.uno.3.º LIVA (semilla por defecto)."*.
This is the legally-correct classification for dental clinical
services in Spain.

The admin can override any row from `/settings/verifactu/vat-mapping`,
including reverting to *Auto* (heuristic) or picking any of the 10
AEAT classifications.

### Heuristic (fallback when no override)

| Rate | Classification | Causa |
|---|---|---|
| 21 / 10 / 4 | `S1` | — |
| 0 (with `vat_exempt_reason` on the line) | `OperacionExenta=E1` | E1 |
| 0 (no exempt reason) | `N1` | — |
| Other | `ValueError` |

---

## 7. Test vs production environments

The only differences between `test` and `prod` are two URLs:

**SOAP submission endpoint** (`services/aeat_client.py`):
```python
"test": "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
"prod": "https://www1.agenciatributaria.gob.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
```

**QR code host** (`services/qr.py`):
```python
_TEST_HOST = "prewww1.aeat.es"
_PROD_HOST = "www1.agenciatributaria.gob.es"
```

Everything else is identical: XML, hash chain, mTLS handshake,
worker, persistence, retry behaviour. There is no mock or dry-run.

**Implications:**
- Test mode hits AEAT's real preproduction sandbox (separate database,
  separate certificates allowed, no fiscal effect).
- Production mode hits the real AEAT. Every record becomes part of the
  clinic's official fiscal ledger.
- Pre-prod and prod are **separate AEAT systems** — what's in test is
  not in prod and vice-versa.
- AEAT pre-prod tends to be unstable. Random `Codigo[103]` errors and
  `503` responses are **AEAT-side**, not client bugs (see §8).
- Switching `prod → test` mid-stream doesn't break our local hash
  chain (the chain is global per NIF), but AEAT will see gaps in
  whichever environment was skipped.

The same uploaded certificate works in both environments — TLS doesn't
differ. AEAT pre-prod accepts: real FNMT certs, AEAT-issued test certs
(e.g. `00000000T Nombre ApellidoUnoÑ (R: Q0000000J)`). Prod requires
real FNMT certs only.

---

## 8. AEAT validation errors — catalogue

Real errors observed during preproduction integration, with root
cause and fix. Use this as a debugging checklist when records appear
in `Errores temporales` or `Rechazados`.

### Codigo[103] — "Error interno del Servidor, Id. del Error: null"

**HTTP 403 + SOAP Fault on `prewww1.aeat.es`.**

Documented as **AEAT-side DB2 write failure**. Their internal
validator died before assigning an incident ID. Same family as
`Codigo[-904]` (resource unavailable).

| Cause | AEAT internal infrastructure |
|---|---|
| Fix | Wait for AEAT to restore. The worker auto-retries every 60 s. |

### Codigo[4102] — "El XML no cumple el esquema. Falta informar campo obligatorio.: Cabecera"

XML schema violation. The validator looked for `Cabecera` in the
namespace it expected and didn't find it.

| Cause | SOAP envelope namespaces inverted: `sum:` was bound to SuministroInformacion, but AEAT expects it bound to SuministroLR (`Cabecera`, `RegFactuSistemaFacturacion`, `RegistroFactura` live in LR; `ObligadoEmision` and inner data elements live in Information). |
|---|---|
| Fix | `templates/soap_envelope.xml.j2`: `xmlns:sum="…SuministroLR.xsd"` and default `xmlns="…SuministroInformacion.xsd"`. Inner elements (`ObligadoEmision`, `RegistroAlta`, `IDFactura`, `Desglose`, …) carry no prefix and inherit the default namespace. |

### Codigo[1237] — "CalificacionOperacion N1/N2 con IVA. No se puede informar TipoImpositivo, CuotaRepercutida…"

Business validation. The line declares "no sujeta" but carries IVA
quota fields.

| Cause | `iva_classifier.classify` returned `tipo_impositivo=Decimal("0")` for `vat_rate=0` (N1). The XML emitted `<TipoImpositivo>0.00</TipoImpositivo>` and `<CuotaRepercutida>0.00</CuotaRepercutida>`, both forbidden under N1/N2. |
|---|---|
| Fix | Set `tipo_impositivo=None` for N1. In `hook._build_desglose`, also force `cuota_repercutida=None` when `calificacion_operacion in ("N1","N2")` or `operacion_exenta=True`. |

### Codigo[4109] — "Error en el bloque de SistemaInformatico. El formato del NIF es incorrecto."

The producer NIF doesn't satisfy AEAT's CIF/DNI check-digit
algorithm.

| Cause | `Q0000000J` (the AEAT test issuer NIF) was used as `producer_nif`. Q0000000J is accepted as `IDEmisorFactura` (special test census entry) but AEAT validates the SIF producer NIF strictly. The standard check digit for `Q0000000` is `A`, not `J`. |
|---|---|
| Fix | Use a real CIF (your real software vendor entity) or a structurally-valid test CIF. Update via `/settings/verifactu/producer` wizard. |

### Codigo[1100] — "Valor o tipo incorrecto del campo: IdSistemaInformatico"

The 2-character system identifier is malformed.

| Cause | `IdSistemaInformatico` must be exactly 2 alphanumeric characters. Empty, longer values or non-alphanumeric chars trigger this. |
|---|---|
| Fix | Set in producer wizard. `DP` is a safe default. |

### Codigo[1103] — "El valor del campo ID es incorrecto"

Generic ID validation. Triggered by malformed `IDFactura` blocks
(e.g. wrong issuer NIF format, invalid date `FechaExpedicionFactura`,
empty `NumSerieFactura`).

| Fix | Inspect the record's `xml_payload` and confirm: NIF uppercase 9 chars, fecha `DD-MM-YYYY`, numerador no vacío. |

### General principle

If the error code is **numeric ≥ 1000** with a meaningful description,
it's an AEAT business validation — fix on the client side. If the
code is `103` / `-904` / `null` / 5xx → AEAT-side, just wait.

The full official error catalogue is at
[Validaciones_Errores_Veri-Factu.pdf](https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Validaciones_Errores_Veri-Factu.pdf).

---

## 9. Troubleshooting

### "Verifactu emitido pero no aparece en cola"

The hook only runs on the `draft → issued` transition. If the
invoice was issued **before** Verifactu was activated (or while
producer signature was revoked), no record exists.

```sql
-- Diagnostic
SELECT enabled FROM verifactu_settings;
SELECT compliance_data FROM invoices WHERE invoice_number = 'FAC-XXXX';
SELECT * FROM verifactu_records WHERE serie_numero = 'FAC-XXXX';
```

The invoice cannot retroactively enter Verifactu after issuance.
Workaround: emit a credit note (R1) referencing the original, then
emit a new invoice with the same items — both will queue normally.

### "El productor wizard no me deja editar tras firmar"

By design — the signature attests to specific data. Click
**"Anular firma para editar"** in the Step 1 alert. This:
- Clears `declaracion_responsable_signed_at` / `_by`.
- Forces `enabled=false`.
- Unlocks fields.

After re-signing, you must reactivate Verifactu manually from the
verifactu home.

### "Tras anular firma, las facturas siguientes no entran a Verifactu"

`enabled` is forced to `false` on revoke. Re-sign + go to
`/settings/verifactu` + click **Activar Verifactu**.

### "Modal en blanco al confirmar producción / anular firma"

Stale frontend cache. Hard-refresh (Cmd+Shift+R).
Modals use Nuxt UI v4 syntax: `<UModal v-model:open="…">` plus
`<template #content>` slot.

### "AEAT 4109 con cert real pero clinic NIF de pruebas"

Mismatch: cert holder ≠ ObligadoEmision. AEAT verifies the cert NIF
matches `IDEmisorFactura` (or is an authorized representative).
Either:
- Update `clinic.tax_id` to your real NIF (matches cert).
- Or use AEAT's test cert (`00000000T … (R: Q0000000J)`) with
  `clinic.tax_id = Q0000000J`.

Mixing real cert + test issuer NIF (or vice versa) → 4109.

### Reset everything for a clean test

```sql
-- Wipe failed records + reset chain head + clear ES compliance.
DELETE FROM verifactu_records WHERE state IN ('failed_transient','rejected','pending');
UPDATE verifactu_settings SET last_huella=NULL, last_record_id=NULL, next_send_after=NULL;
UPDATE invoices SET compliance_data = compliance_data - 'ES' WHERE compliance_data ? 'ES';
```

DO NOT delete records in `state='accepted'` — they're legally
retained for 4 years.

---

## 10. Data model

### `verifactu_settings` — one row per clinic

| Column | Type | Purpose |
|---|---|---|
| `clinic_id` | UUID, unique | Owner |
| `enabled` | bool | Hook only acts if true |
| `environment` | `test` / `prod` | AEAT endpoint |
| `numero_instalacion` | str(60) | UUID per clinic for `<NumeroInstalacion>` |
| `last_huella` | str(64) | Chain head SHA-256 |
| `last_record_id` | UUID | FK to last accepted record |
| `next_send_after` | timestamptz | AEAT-imposed back-pressure |
| `last_aeat_response_at` | timestamptz | Diagnostics |
| `producer_nif` | str(20) | NIF of the SIF producer |
| `producer_name` | str(200) | Producer legal name |
| `producer_id_sistema` | str(2) | 2-char system ID, default `DP` |
| `producer_version` | str(20) | Software version string |
| `declaracion_responsable_signed_at` | timestamptz | Sealed when wizard signed |
| `declaracion_responsable_signed_by` | UUID FK users | Auditor of the signature |

The clinic's NIF and legal name are NOT duplicated here — they live
in `clinics.tax_id` and `clinics.legal_name` (single source of truth).

### `verifactu_certificates` — encrypted PFX storage

| Column | Purpose |
|---|---|
| `pfx_encrypted` | Fernet-encrypted PFX bytes |
| `password_encrypted` | Fernet-encrypted password |
| `subject_cn`, `issuer_cn`, `nif_titular` | Display metadata |
| `valid_from`, `valid_until` | Expiry banner thresholds |
| `is_active` | One active per clinic (partial unique idx) |
| `uploaded_by` | Audit |

### `verifactu_records` — append-only fiscal ledger

Legal retention: 4 years (LGT plazo de prescripción).

| Column | Purpose |
|---|---|
| `clinic_id`, `invoice_id` | Multi-tenant filtering |
| `record_type` | `alta` / `anulacion` |
| `tipo_factura` | F1, F2, F3, R1, R2, R3, R4, R5 |
| `huella`, `huella_anterior`, `is_first_record` | Chain links |
| `xml_payload` | Verbatim XML — legal req |
| `state` | `pending`, `sending`, `accepted`, `accepted_with_errors`, `rejected`, `failed_transient`, `failed_validation` |
| `aeat_csv` | AEAT receipt code |
| `aeat_estado_envio` / `aeat_estado_registro` | Response status |
| `aeat_codigo_error` / `aeat_descripcion_error` | Real AEAT codes (positive ints) or sentinels: `-1`=transport, `-2`=SOAP Fault |
| `aeat_response_xml` | Raw response for forensics |

Indexes: `(clinic_id, created_at desc)`, `(clinic_id, state)`,
`(invoice_id)`, **unique** `(clinic_id, huella)`.

### `verifactu_vat_classifications` — AEAT mapping per VAT type

| Column | Purpose |
|---|---|
| `clinic_id`, `vat_type_id` | Composite key (unique) |
| `classification` | `S1`, `S2`, `E1`-`E6`, `N1`, `N2` |
| `exemption_cause` | `E1`-`E6` (redundant of classification when exempt) |
| `notes` | Free text legal reference |

---

## 11. API endpoints

Base prefix: `/api/v1/verifactu/`. Every endpoint requires
`ClinicContext` (auth + clinic membership).

| Method | Path | Permission | Notes |
|---|---|---|---|
| GET | `/settings` | `verifactu.settings.read` | Read or lazily create. NIF emisor / razón social derived from `clinics`. |
| PUT | `/settings` | `verifactu.settings.configure` | Toggle enabled / environment. Auto-sets `clinic.settings.country='ES'` when enabled. Rejects enable if any prereq missing. |
| GET | `/producer/defaults` | `verifactu.settings.read` | Env-var defaults for the wizard |
| PUT | `/producer` | `verifactu.settings.configure` | Wizard: write producer info + sign |
| DELETE | `/producer/declaracion` | `verifactu.settings.configure` | Revoke signature + force-disable Verifactu |
| POST | `/certificate` | `verifactu.settings.configure` | Multipart upload (`file=*.pfx`, `password=...`) |
| GET | `/certificate` | `verifactu.settings.read` | Active cert metadata |
| GET | `/certificate/history` | `verifactu.settings.read` | All uploaded certs |
| DELETE | `/certificate/{id}` | `verifactu.settings.configure` | Soft-deactivate |
| GET | `/records` | `verifactu.records.read` | Paginated ledger |
| GET | `/records/{id}` | `verifactu.records.read` | Detail incl. XML |
| GET | `/records/{id}/xml` | `verifactu.records.read` | Plain text XML payload |
| GET | `/queue` | `verifactu.queue.manage` | Filter by state |
| POST | `/queue/{id}/retry` | `verifactu.queue.manage` | Mark for resubmit (`Subsanacion=S`) |
| POST | `/queue/process-now` | `verifactu.queue.manage` | Trigger worker for this clinic immediately |
| GET | `/vat-mapping` | `verifactu.settings.read` | List VAT types + AEAT override + inferred default |
| PUT | `/vat-mapping/{vat_type_id}` | `verifactu.settings.configure` | Upsert/clear override |
| GET | `/health` | `verifactu.settings.read` | Summary: enabled, env, has_cert, valid_until, pending+rejected |

**Immutable**: no endpoint allows editing `huella`, `xml_payload`,
`aeat_csv` on records. The libro fiscal is append-only by design.

---

## 12. Permissions

Module returns these from `get_permissions()` (registry namespaces
to `verifactu.*`):

```
settings.read
settings.configure
records.read
queue.manage
```

Default role grants:
- `admin` → `*` (all)
- `dentist` → `records.read`
- `hygienist`, `assistant` → none
- `receptionist` → `records.read`

---

## 13. Pre-production checklist

Before flipping any clinic's environment to `prod`:

### Legal & operational

- [ ] Read the AEAT spec PDFs:
  - `Veri-Factu_especificaciones_huella_hash_registros.pdf`
  - `DetalleEspecificacTecnCodigoQRfactura.pdf`
  - `Veri-Factu_Descripcion_SWeb.pdf`
- [ ] Obtain a real FNMT certificate (representante PJ or sello de
  empresa) for the clinic.
- [ ] Decide producer model and sign the declaración responsable in
  the wizard (`/settings/verifactu/producer`).
- [ ] Publish the declaración responsable on your public website AND
  deliver a copy to each clinic that uses the software.
- [ ] Engage gestoría / legal review specialised in SII / Verifactu
  (~500-1500 €). LGT 201 bis exposure makes this worthwhile.
- [ ] Define internal AEAT inspection response process: who receives
  the requerimiento, response window (typically 10 business days),
  evidence package contents.

### Technical validation against `prewww1.aeat.es`

- [ ] Real FNMT cert + minimum 20 invoices covering: F1 with NIF /
  IVA general (21%) / IVA reducido (10%) / sanitario exento (E1) /
  F2 simplificada <400 € / R1 rectificativa / anulación / multi-line
  con IVAs mixtos / subsanación tras rechazo simulado.
- [ ] Verify each `accepted` record's CSV in the AEAT preproduction
  portal manually.
- [ ] Test certificate expiry: load a cert expiring in <60 days and
  confirm the UI shows the amber/red banner.
- [ ] Test mTLS with bad password — must surface a clear error.
- [ ] Concurrency test: emit 100 invoices in parallel, verify the
  chain is intact (no missing or duplicate `huella`).
- [ ] Round-trip uninstall: with no records, uninstall must succeed;
  with `accepted` records, must fail with the legal warning.
- [ ] Restart resilience: kill worker mid-batch, verify
  `state=sending` records get re-picked. (Currently they don't —
  watchdog reaper is a known TODO.)

### Frontend wiring

- [ ] Embed `<InvoiceVerifactuPanel>` in the host's
  `frontend/app/pages/invoices/[id].vue` so users see QR + CSV +
  huella on the invoice detail.
- [ ] Embed the QR in the invoice PDF — `hook.enhance_pdf_data`
  returns `verifactu_qr_png_b64`. Billing's `pdf.py` must place it
  in the upper-right corner per AEAT spec (size 30-40 mm, label
  "QR tributario", text "VERI*FACTU" nearby).
- [ ] Restrict `prod` toggle to admin role (consider a separate
  `verifactu.environment.promote` permission).

### Operational

- [ ] Set production env vars:
  ```
  VERIFACTU_VENDOR_NIF=…
  VERIFACTU_VENDOR_NAME=…
  VERIFACTU_SOFTWARE_VERSION=…  # tied to your deploy tag
  ```
- [ ] Backups: confirm `pg_dump` runs nightly and includes
  `verifactu_records`. Records must survive 4 years.
- [ ] KMS / secret rotation: `SECRET_KEY` derives the Fernet key.
  Rotating it would render every encrypted PFX + password unreadable.
  Document a key-rotation procedure (re-upload all certs after
  rotation) before going live.
- [ ] Monitoring: alert on `next_send_after` slipping > 1 h
  (suggests AEAT outage) and on `rejected` count growing.
- [ ] Refresh AEAT XSDs: vendor schemas may shift. Plan periodic
  refresh from
  `https://prewww2.aeat.es/static_files/.../tikeV1.0/cont/ws/`.

### Module gaps still open

- [ ] **Worker stuck-record reaper** — records in `state=sending`
  after a worker crash are not rescued. Add a watchdog that demotes
  them back to `pending` after 10 minutes.
- [ ] **AEAT error code → user-friendly message map** — translate
  the most common 100 codes from `errores.properties` into Spanish
  strings shown in the queue UI.
- [ ] **Certificate expiry email** — daily APScheduler job that
  emails admins when any clinic's cert expires in <30 days.
- [ ] **PDF embedding of QR** — see frontend wiring TODO above.
- [ ] **`is_exento_sanitario` first-class column on `invoice_items`**
  — currently the hook deduces it from `vat_exempt_reason`.

---

## 14. References

### Official AEAT

- [VERI*FACTU portal — sede AEAT](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu.html)
- [Información técnica — preproducción](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/informacion-tecnica.html)
- [PRE-Exteriores AEAT (preproducción)](https://preportal.aeat.es/PRE-Exteriores/Inicio/_menu_/VERI_FACTU___Sistemas_Informaticos_de_Facturacion/VERI_FACTU___Sistemas_Informaticos_de_Facturacion.html)
- [Portal de desarrolladores AEAT](https://www.agenciatributaria.es/AEAT.desarrolladores/Desarrolladores/_menu_/Documentacion/Sistemas_Informaticos_de_Facturacion_y_Sistemas_VERI_FACTU/Sistemas_Informaticos_de_Facturacion_y_Sistemas_VERI_FACTU.html)
- [Validaciones y errores Veri\*Factu (PDF oficial)](https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Validaciones_Errores_Veri-Factu.pdf)
- [FAQs Desarrolladores Veri\*Factu (PDF oficial)](https://sede.agenciatributaria.gob.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/FAQs-Desarrolladores.pdf)
- [Descripción Servicios Web (PDF oficial)](https://sede.agenciatributaria.gob.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_Descripcion_SWeb.pdf)

### Legal

- [RD 1007/2023 (BOE-A-2023-24840)](https://www.boe.es/buscar/act.php?id=BOE-A-2023-24840)
- [Orden HAC/1177/2024 (BOE-A-2024-22138)](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-22138)

### FNMT certificates

- [Certificado de Representante de Persona Jurídica — solicitud](https://www.sede.fnmt.gob.es/certificados/certificado-de-representante/persona-juridica/solicitar-certificado)
- [Certificados válidos para VERI\*FACTU — FNMT](https://www.sede.fnmt.gob.es/preguntas-frecuentes/certificado-de-persona-fisica/-/asset_publisher/eIal9z2VE0Kb/content/certificados-electr%C3%B3nicos-v%C3%A1lidos-para-el-sistema-veri*factu)

### Reference open-source implementations (for cross-checking XML)

- [EduardoRuizM/verifactu-api-python](https://github.com/EduardoRuizM/verifactu-api-python) — Python Flask, MIT
- [mybooking-es/verifactu-rb](https://github.com/mybooking-es/verifactu-rb) — Ruby, includes XSDs
- [mdiago/VeriFactu](https://github.com/mdiago/VeriFactu) — .NET
- [squareetlabs/verifactu-sdk](https://github.com/squareetlabs/verifactu-sdk) — Java/Maven
- [hectorsipe/aeat-verifactu](https://github.com/hectorsipe/aeat-verifactu) — XSD mirror

### Endpoints

| Environment | URL |
|---|---|
| Test (preproducción) | `https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP` |
| Production | `https://www1.agenciatributaria.gob.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP` |
| Test QR validation | `https://prewww1.aeat.es/wlpl/TIKE-CONT/ValidarQR` |
| Production QR validation | `https://www1.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR` |

### Support

For preproduction outages or specific developer questions:
**verifactu@correo.aeat.es**.
