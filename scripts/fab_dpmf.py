"""Fabricate a synthetic DPMF v0.1 file for end-to-end migration_import testing.

Self-contained — only uses Python stdlib. Writes a raw (uncompressed,
unencrypted) ``.dpm`` SQLite container with 100 patients and a full
spread of associated entities (treatments, alerts, medical history,
budgets, fiscal documents, payments, appointments, clients).

Run inside the backend container so the SQLite + json available there
match what the importer will read:

    docker compose exec -T backend python /app/../scripts/fab_dpmf.py /tmp/fake_clinica.dpm
"""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid5

CANONICAL_NS = UUID("dde7d63a-1f43-4ed8-8b91-67b5e9c7c0f7")
SOURCE_SYSTEM = "gesden"
TENANT = "fake-clinic"
FORMAT_VERSION = "0.1.0"


def cuuid(entity_type: str, source_id: str) -> str:
    return str(uuid5(CANONICAL_NS, f"{SOURCE_SYSTEM}:{entity_type}:{source_id}"))


def iso(value: datetime | date) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return value.isoformat()


NOW = datetime.now(UTC)


def init_db(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA user_version = 1")
    conn.executescript("""
        CREATE TABLE _meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE _entities (
            entity_type    TEXT PRIMARY KEY,
            row_count      INTEGER NOT NULL,
            schema_version TEXT NOT NULL
        );
        CREATE TABLE _files (
            canonical_uuid TEXT PRIMARY KEY,
            parent_entity_type TEXT NOT NULL,
            parent_canonical_uuid TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            declared_size_bytes INTEGER,
            sha256 TEXT,
            mime_hint TEXT
        );
        CREATE INDEX idx_files_parent ON _files(parent_entity_type, parent_canonical_uuid);
        CREATE TABLE _warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            source_id TEXT,
            severity TEXT NOT NULL CHECK (severity IN ('info','warn','error')),
            code TEXT NOT NULL,
            message TEXT NOT NULL,
            raw_data TEXT CHECK (raw_data IS NULL OR json_valid(raw_data))
        );
    """)
    return conn


def write_meta(conn: sqlite3.Connection) -> None:
    items = {
        "format_version": FORMAT_VERSION,
        "source_system": SOURCE_SYSTEM,
        "source_adapter_version": "0.1.0",
        "source_schema_fingerprint": "",
        "exporter_tool": "dental-bridge",
        "exporter_version": "0.1.0",
        "exported_at": iso(NOW),
        "tenant_label": TENANT,
        "integrity_hash_algo": "sha256",
        "integrity_hash": "PENDING",
    }
    conn.executemany("INSERT INTO _meta(key,value) VALUES (?,?)", items.items())


KNOWN_TABLES: set[str] = set()


def ensure_table(conn: sqlite3.Connection, entity_type: str) -> None:
    if entity_type in KNOWN_TABLES:
        return
    conn.execute(f'''
        CREATE TABLE IF NOT EXISTS "{entity_type}" (
            canonical_uuid TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            source_system TEXT NOT NULL,
            payload TEXT NOT NULL CHECK (json_valid(payload)),
            raw_source_data TEXT NOT NULL CHECK (json_valid(raw_source_data)),
            extracted_at TEXT NOT NULL
        )
    ''')
    conn.execute(
        f'CREATE INDEX IF NOT EXISTS "idx_{entity_type}_source" ON "{entity_type}"(source_system, source_id)'
    )
    KNOWN_TABLES.add(entity_type)


def append(
    conn: sqlite3.Connection,
    entity_type: str,
    source_id: str,
    payload: dict,
    raw: dict | None = None,
) -> str:
    ensure_table(conn, entity_type)
    canonical_uuid = cuuid(entity_type, source_id)
    full_payload = {
        "canonical_uuid": canonical_uuid,
        "source_system": SOURCE_SYSTEM,
        "entity_type": entity_type,
        "source_id": source_id,
        "adapter_version": "0.1.0",
        "extracted_at": iso(NOW),
        "raw_source_data": raw or {},
        **payload,
    }
    conn.execute(
        f'INSERT OR REPLACE INTO "{entity_type}"'
        " (canonical_uuid, source_id, source_system, payload, raw_source_data, extracted_at)"
        " VALUES (?,?,?,?,?,?)",
        (
            canonical_uuid,
            source_id,
            SOURCE_SYSTEM,
            json.dumps(full_payload, default=str, ensure_ascii=False),
            json.dumps(raw or {}, default=str, ensure_ascii=False),
            iso(NOW),
        ),
    )
    return canonical_uuid


def finalise(conn: sqlite3.Connection, counts: dict[str, int]) -> None:
    for et, count in counts.items():
        conn.execute(
            "INSERT INTO _entities(entity_type,row_count,schema_version) VALUES (?,?,?)",
            (et, count, "0.1.0"),
        )
    conn.commit()

    hasher = hashlib.sha256()
    for row in conn.execute(
        "SELECT entity_type,row_count,schema_version FROM _entities ORDER BY entity_type"
    ):
        hasher.update(f"_entities|{row[0]}|{row[1]}|{row[2]}\n".encode())
    for et in sorted(KNOWN_TABLES):
        for row in conn.execute(
            f'SELECT canonical_uuid,source_id,source_system,payload,raw_source_data FROM "{et}" ORDER BY canonical_uuid'
        ):
            hasher.update(f"{et}|{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}\n".encode())
    for row in conn.execute(
        "SELECT canonical_uuid,parent_entity_type,parent_canonical_uuid,relative_path,declared_size_bytes,sha256,mime_hint FROM _files ORDER BY canonical_uuid"
    ):
        hasher.update(("_files|" + "|".join(str(v) for v in row) + "\n").encode())
    for row in conn.execute(
        "SELECT id,entity_type,source_id,severity,code,message,raw_data FROM _warnings ORDER BY id"
    ):
        hasher.update(("_warnings|" + "|".join(str(v) for v in row) + "\n").encode())
    conn.execute("UPDATE _meta SET value=? WHERE key='integrity_hash'", (hasher.hexdigest(),))
    conn.commit()


# --- Data fabrication -------------------------------------------------------

GIVEN_NAMES = [
    "María", "José", "Carmen", "Antonio", "Juan", "Pilar", "Manuel", "Ana",
    "Francisco", "Laura", "Javier", "Isabel", "Carlos", "Lucía", "David",
    "Marta", "Daniel", "Cristina", "Pedro", "Sara", "Pablo", "Elena",
    "Alberto", "Andrea", "Sergio", "Patricia", "Luis", "Beatriz",
]
FAMILY_NAMES = [
    "García", "Rodríguez", "Martínez", "López", "Sánchez", "Pérez", "Gómez",
    "Fernández", "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Álvarez",
    "Muñoz", "Romero", "Alonso", "Gutiérrez", "Navarro", "Torres",
]
CITIES = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Zaragoza"]
ALLERGIES = [
    "Penicilina", "Látex", "AINEs", "Aspirina", "Anestésicos locales",
    "Yodo", "Sulfamidas",
]
DISEASES = [
    "Hipertensión arterial", "Diabetes Mellitus tipo II", "Asma bronquial",
    "Hipotiroidismo", "Arritmia cardíaca", "Osteoporosis", "Reflujo gastroesofágico",
]
MEDICATIONS = [
    ("Omeprazol", "20 mg", "1 cápsula al día"),
    ("Enalapril", "10 mg", "1 comprimido cada 12 h"),
    ("Metformina", "850 mg", "1 comprimido cada 8 h"),
    ("Levotiroxina", "75 mcg", "1 comprimido en ayunas"),
    ("Atorvastatina", "20 mg", "1 comprimido por la noche"),
]
TREATMENT_CATALOG = [
    # (name, IdTipoOdg, base_price, is_global_mouth)
    # Per-tooth clinical IdTipoOdg codes — DentalPin doesn't have a 1:1
    # match for these in its clinical_type enum, so the importer warns
    # ``applied_treatment.unmapped_tipo_odg`` and falls back to
    # ``migrated``; that's expected behaviour for synthetic fixtures.
    ("Empaste composite", 20, 65.00, False),
    ("Endodoncia molar", 22, 220.00, False),
    ("Corona ceramo-metálica", 23, 480.00, False),
    ("Implante dental", 24, 950.00, False),
    ("Extracción simple", 25, 45.00, False),
    # Non-clinical IdTipoOdg codes that the importer routes through
    # ``_NON_CLINICAL_TIPO_ODG`` → Treatment(scope='global_mouth') +
    # PlannedTreatmentItem + PatientEarnedEntry.
    ("Limpieza dental (higiene)", 38, 55.00, True),
    ("Radiografía panorámica", 39, 35.00, True),
    ("Primera visita", 13, 0.00, True),
    ("Bonos ortodoncia", 14, 90.00, True),
    ("Fluorización", 41, 320.00, True),
]
STATUS_CODES = [3, 5, 6]  # 3 planned, 5/6 realised
ROLE_BY_INDEX = ["dentist", "hygienist", "dentist", "assistant", "dentist"]

# Per-treatment notes — picked at random so migrated treatments
# carry realistic, varied clinical narrative instead of a single
# placeholder string.
TREATMENT_NOTES = [
    "Anestesia con lidocaína 2% sin epinefrina. Sin incidencias intraoperatorias.",
    "Tallado conservador con preservación de esmalte. Aislamiento absoluto con dique.",
    "Composite A2 estratificado en tres capas. Polimerización 20s por capa.",
    "Endodoncia en dos sesiones. Obturación con gutapercha + sellador AH Plus.",
    "Paciente refiere sensibilidad post-operatoria leve. Citado a control en 7 días.",
    "Implante 4.1x10mm Straumann SLA. Torque de inserción 35 Ncm. Tapa de cicatrización colocada.",
    "Provisional acrílico ajustado. Próxima sesión: prueba metal-cerámica.",
    "Corona definitiva cementada con ionómero de vidrio. Oclusión revisada y ajustada.",
    "Extracción sin complicaciones. Hemostasia con compresión y sutura 4-0 reabsorbible.",
    "Limpieza con ultrasonidos + pulido con copa de goma. Profilaxis con flúor tópico.",
    "Radiografía panorámica de control. Sin hallazgos patológicos significativos.",
    "Revisión post-tratamiento: cicatrización óptima. Paciente sin molestias.",
    "Sellado de fosas y fisuras en molar permanente. Indicado por riesgo de caries elevado.",
    "Apicectomía con obturación retrógrada MTA. Sutura 5-0. Antibiótico profiláctico recetado.",
    "Blanqueamiento ambulatorio con peróxido carbamida 16% en férula. Resultado: -3 tonos en Vita.",
]

# Per-patient narrative templates — placeholders ({alergia}, {enfermedad})
# are filled at fab time so each patient has a distinct medical
# context. Tests that the per-row notes reach the patient profile
# alert classifier as designed.
PATIENT_NOTES = [
    "Paciente con {enfermedad} controlada. Alergia a {alergia}. Última visita sin incidencias.",
    "Antecedentes: {enfermedad}. Toma medicación habitual. Sin alergias conocidas.",
    "Sensibilidad dentinaria generalizada. Bruxismo nocturno; usa férula. Sin patologías sistémicas.",
    "Paciente embarazada (2º trimestre). Posponer radiografías no urgentes. Revisión de higiene reforzada.",
    "Reacción anterior a {alergia} — confirmar antes de prescribir antibióticos o analgésicos.",
    "Historial de {enfermedad}. Recomendado seguimiento semestral. Recall periodontal activo.",
    "Paciente con prótesis parcial removible superior. Buena higiene oral. Sin patologías relevantes.",
    "Tratamiento de ortodoncia en curso (brackets). Cita mensual para ajuste. Higiene buena.",
    "Fumador (15 cig/día). Riesgo periodontal moderado. Recall trimestral. Educación en higiene.",
    "Paciente con ansiedad dental severa. Manejo con técnicas conductuales. Anestesia tópica previa.",
]

# Standalone Gesdén users (administrativos, recepción, contabilidad).
# Generated so `user_uuid` references on budgets/payments/etc. can be
# resolved by the importer instead of falling back to the migration
# admin. Each tuple: (source_id, given_name, family_name, email, role-hint-only)
GESDEN_USERS = [
    ("USR1", "Carmen", "Vidal", "admin@clinica-demo.local", "Administradora"),
    ("USR2", "Lucía", "Pérez", "recepcion.am@clinica-demo.local", "Recepción mañana"),
    ("USR3", "Sara", "López", "recepcion.pm@clinica-demo.local", "Recepción tarde"),
    ("USR4", "Mateo", "Ruiz", "contabilidad@clinica-demo.local", "Contabilidad"),
]


def fab(conn: sqlite3.Connection) -> dict[str, int]:
    rnd = random.Random(20260521)
    counts: dict[str, int] = {}

    def bump(et: str, n: int = 1) -> None:
        counts[et] = counts.get(et, 0) + n

    # --- Center ---
    append(conn, "center", "C1", {
        "name": "Clínica Fake Demo",
        "address": "Calle Mayor 1",
        "tenant_label": TENANT,
    })
    bump("center")

    # --- Professionals (5) ---
    professionals = []
    for i in range(5):
        sid = f"P{i + 1}"
        professionals.append(cuuid("professional", sid))
        append(conn, "professional", sid, {
            "code": sid,
            "given_name": GIVEN_NAMES[i],
            "family_name": FAMILY_NAMES[i],
            "national_id": f"5000000{i}A",
            "role": ROLE_BY_INDEX[i],
            "email": f"prof{i + 1}@fake.demo",
            "phone": f"60000000{i}",
            "deactivated": False,
            "tenant_label": TENANT,
        })
        bump("professional")

    # --- Standalone users (non-clinical staff in Gesdén) ---
    user_uuids: list[str] = []
    for sid, given, family, email, _ in GESDEN_USERS:
        u_uuid = append(conn, "user", sid, {
            "login": email,
            "given_name": given,
            "family_name": family,
            "email": email,
            "deactivated": False,
            "tenant_label": TENANT,
        })
        user_uuids.append(u_uuid)
        bump("user")

    # --- Treatment catalog items + variants ---
    catalog_uuids: list[tuple[str, float, bool]] = []  # (variant_uuid, price, is_global)
    for idx, (name, tipo_odg, price, is_global) in enumerate(TREATMENT_CATALOG, start=1):
        item_sid = f"TC{idx}"
        # Per `CanonicalTreatmentCatalogItem` spec: the display label
        # lives in ``short_name`` / ``description`` / ``agenda_description``,
        # not ``name`` (the canonical has no ``name`` field). Setting
        # only ``name`` caused the catalog mapper's fallback chain to
        # land on ``code`` and clinics saw "COD004" in the UI.
        item_uuid = append(conn, "treatment_catalog_item", item_sid, {
            "short_name": name,
            "description": name,
            "code": f"COD{idx:03d}",
            "deactivated": False,
            "reference_price": str(price),
            "tenant_label": TENANT,
        }, raw={"IdTipoOdg": tipo_odg})
        bump("treatment_catalog_item")
        var_sid = f"TCV{idx}"
        variant_uuid = append(conn, "treatment_catalog_variant", var_sid, {
            "treatment_uuid": item_uuid,
            "tariff_code": "STD",
            "code": f"VAR{idx:03d}",
            "unit_price": str(price),
            "tenant_label": TENANT,
        }, raw={"IdTipoOdg": tipo_odg})
        bump("treatment_catalog_variant")
        catalog_uuids.append((variant_uuid, price, is_global))

    # --- 100 patients + 1 client each ---
    patients: list[tuple[str, str, str]] = []  # (patient_uuid, client_uuid, patient_sid)
    for pi in range(1, 101):
        sid = f"PAT{pi:04d}"
        gname = rnd.choice(GIVEN_NAMES)
        fname = f"{rnd.choice(FAMILY_NAMES)} {rnd.choice(FAMILY_NAMES)}"
        dob = date(rnd.randint(1940, 2015), rnd.randint(1, 12), rnd.randint(1, 28))
        sex = rnd.choice(["male", "female", "unknown"])
        registered = date(rnd.randint(2010, 2024), rnd.randint(1, 12), rnd.randint(1, 28))
        # ~40% of patients carry a clinical narrative; pick a varied
        # template and fill placeholders so each row is distinct.
        if pi % 5 not in (0, 3):
            notes = None
        else:
            template = rnd.choice(PATIENT_NOTES)
            notes = template.format(
                alergia=rnd.choice(ALLERGIES),
                enfermedad=rnd.choice(DISEASES),
            )
        p_uuid = append(conn, "patient", sid, {
            "patient_number": f"{pi:05d}",
            "given_name": gname,
            "family_name": fname,
            "national_id": f"{10000000 + pi:08d}Z",
            "date_of_birth": iso(dob),
            "sex": sex,
            "registered_at": iso(registered),
            "deceased": False,
            "gdpr_consent": True,
            "notes": notes,
            "default_professional_uuid": professionals[pi % 5],
            "tenant_label": TENANT,
        })
        bump("patient")

        client_sid = f"CLI{pi:04d}"
        c_uuid = append(conn, "client", client_sid, {
            "kind": "person",
            "given_name": gname,
            "family_name": fname,
            "national_id": f"{10000000 + pi:08d}Z",
            "email": f"cliente{pi}@fake.demo",
            "tenant_label": TENANT,
        })
        bump("client")

        # Link client → patient
        link_sid = f"PCL{pi:04d}"
        append(conn, "patient_client_link", link_sid, {
            "patient_uuid": p_uuid,
            "client_uuid": c_uuid,
            "valid_from": iso(registered),
        })
        bump("patient_client_link")
        patients.append((p_uuid, c_uuid, sid))

    # --- Per-patient: alerts, history, appointments, treatments, budgets,
    # ---            fiscal docs, payments ---
    next_atid = 1
    next_phaseid = 1
    next_apptid = 1
    next_alertid = 1
    next_pharmid = 1
    next_budgetid = 1
    next_blineid = 1
    next_fdocid = 1
    next_flineid = 1
    next_payid = 1

    for pi, (p_uuid, c_uuid, p_sid) in enumerate(patients, start=1):
        prof_uuid = professionals[pi % 5]

        # ---- Alerts (1 every patient, 2 for 30%) ----
        for _ in range(1 + (1 if rnd.random() < 0.3 else 0)):
            alert_sid = f"ALR{next_alertid:05d}"
            next_alertid += 1
            allergy = rnd.choice(ALLERGIES)
            append(conn, "patient_alert", alert_sid, {
                "patient_uuid": p_uuid,
                "text": f"Alergia a {allergy}. Confirmar antes de prescribir.",
                "flagged": True,
                "tenant_label": TENANT,
            })
            bump("patient_alert")

        # ---- Pharmacological history (1 for 40%, 2 for 20%) ----
        n_pharm = 0
        if rnd.random() < 0.6:
            n_pharm = 1
        if rnd.random() < 0.2:
            n_pharm = 2
        for _ in range(n_pharm):
            pharm_sid = f"PHM{next_pharmid:05d}"
            next_pharmid += 1
            name, dose, freq = rnd.choice(MEDICATIONS)
            append(conn, "pharmacological_history", pharm_sid, {
                "patient_uuid": p_uuid,
                "professional_uuid": prof_uuid,
                "drug_description": name,
                "dose": dose,
                "frequency": freq,
                "observations": f"Indicación por {rnd.choice(DISEASES)}",
                "record_kind": 1,
                "tenant_label": TENANT,
            })
            bump("pharmacological_history")

        # ---- Appointments (0-2) ----
        for _ in range(rnd.randint(0, 2)):
            appt_sid = f"APT{next_apptid:05d}"
            next_apptid += 1
            offset_days = rnd.randint(-365, 60)
            scheduled = date.today() + timedelta(days=offset_days)
            scheduled_time = f"{rnd.randint(9, 19):02d}:{rnd.choice(['00','15','30','45'])}:00"
            status = (
                "attended" if offset_days < 0
                else rnd.choice(["scheduled", "confirmed"])
            )
            append(conn, "appointment", appt_sid, {
                "patient_uuid": p_uuid,
                "professional_uuid": prof_uuid,
                "scheduled_date": iso(scheduled),
                "scheduled_time": scheduled_time,
                "duration_minutes": rnd.choice([30, 45, 60]),
                "coarse_status": status,
                "notes": "Migrado desde Gesdén — sin observaciones.",
                "tenant_label": TENANT,
            })
            bump("appointment")

        # ---- Applied treatments (1-3) ----
        patient_treatments: list[tuple[str, float, str, bool]] = []  # (uuid, amount, variant_uuid, is_global)
        for _ in range(rnd.randint(1, 3)):
            at_sid = f"TTM{next_atid:05d}"
            next_atid += 1
            variant_uuid, price, is_global = rnd.choice(catalog_uuids)
            start = date.today() - timedelta(days=rnd.randint(30, 2400))
            status_code = rnd.choice(STATUS_CODES)
            end_dt = start + timedelta(days=rnd.randint(0, 90)) if status_code in (5, 6) else None
            amount = round(price * rnd.uniform(0.9, 1.1), 2)
            # decode teeth for non-global treatments
            tooth = rnd.choice([11, 12, 13, 14, 21, 22, 31, 32, 41, 42, 46, 36]) if not is_global else None
            payload = {
                "patient_uuid": p_uuid,
                "client_uuid": c_uuid,
                "professional_uuid": prof_uuid,
                "user_uuid": rnd.choice(user_uuids),
                "treatment_variant_uuid": variant_uuid,
                "status_code": status_code,
                "start_date": iso(start),
                "end_date": iso(end_dt) if end_dt else None,
                "amount": str(amount),
                "units": 1,
                "notes": rnd.choice(TREATMENT_NOTES),
                "teeth": [tooth] if tooth else [],
                "tenant_label": TENANT,
            }
            # Get IdTipoOdg from catalog index. Need to look up via variant.
            # Simpler: stash a synthetic raw with IdTipoOdg matching catalog.
            cat_idx = next(
                i for i, (vu, _, _) in enumerate(catalog_uuids) if vu == variant_uuid
            )
            id_tipo_odg = TREATMENT_CATALOG[cat_idx][1]
            raw = {"IdTipoOdg": id_tipo_odg, "FecIni": iso(start)}
            at_uuid = append(conn, "applied_treatment", at_sid, payload, raw=raw)
            bump("applied_treatment")
            patient_treatments.append((at_uuid, amount, variant_uuid, is_global))

            # 50% chance of an applied_treatment_phase
            if rnd.random() < 0.5:
                ph_sid = f"PHS{next_phaseid:05d}"
                next_phaseid += 1
                append(conn, "applied_treatment_phase", ph_sid, {
                    "applied_treatment_uuid": at_uuid,
                    "professional_uuid": prof_uuid,
                    "phase_number": 1,
                    "status_code": status_code,
                    "executed_on": iso(end_dt or start),
                    "percent_to_bill": "100",
                    "notes": "Fase única.",
                    "tenant_label": TENANT,
                })
                bump("applied_treatment_phase")

        # ---- Budget (1 per patient, lines = treatments) ----
        if patient_treatments:
            b_sid = f"BDG{next_budgetid:04d}"
            next_budgetid += 1
            quote_dt = date.today() - timedelta(days=rnd.randint(60, 1200))
            accepted = rnd.random() < 0.8
            b_uuid = append(conn, "budget", b_sid, {
                "patient_uuid": p_uuid,
                "professional_uuid": prof_uuid,
                "elaborated_by_user_uuid": rnd.choice(user_uuids),
                "number": pi,
                "title": f"Presupuesto plan {quote_dt.year}",
                "quote_date": iso(quote_dt),
                "accepted_date": iso(quote_dt + timedelta(days=3)) if accepted else None,
                "status_code": 2 if accepted else 1,
                "tenant_label": TENANT,
            })
            bump("budget")
            for line_no, (at_uuid, amount, variant_uuid, _is_global) in enumerate(patient_treatments, start=1):
                line_sid = f"BLN{next_blineid:05d}"
                next_blineid += 1
                append(conn, "budget_line", line_sid, {
                    "budget_uuid": b_uuid,
                    "patient_uuid": p_uuid,
                    "treatment_variant_uuid": variant_uuid,
                    "applied_treatment_uuid": at_uuid if accepted else None,
                    "line_number": line_no,
                    "order_within_budget": line_no,
                    "units": "1",
                    "unit_amount": str(amount),
                    "list_amount": str(amount),
                    "base_amount": str(amount),
                    "vat_percent": "0",
                    "vat_amount": "0",
                    "tenant_label": TENANT,
                })
                bump("budget_line")

        # ---- Fiscal document (one per realised cohort) ----
        realised_treatments = [
            (at_uuid, amount, variant_uuid)
            for (at_uuid, amount, variant_uuid, _is_global) in patient_treatments
            if amount > 0
        ]
        if realised_treatments and rnd.random() < 0.7:
            fd_sid = f"FDC{next_fdocid:05d}"
            next_fdocid += 1
            issued = date.today() - timedelta(days=rnd.randint(5, 800))
            total = round(sum(a for _, a, _ in realised_treatments), 2)
            subtotal = round(total / 1.21, 2)
            tax = round(total - subtotal, 2)
            fd_uuid = append(conn, "fiscal_document", fd_sid, {
                "client_uuid": c_uuid,
                "patient_uuid": p_uuid,
                "user_uuid": rnd.choice(user_uuids),
                "series": "F",
                "number": str(next_fdocid - 1),
                "year": issued.year,
                "document_kind": "F",
                "document_date": iso(issued),
                "issued_at": iso(issued),
                "subtotal": str(subtotal),
                "tax_total": str(tax),
                "total": str(total),
                "status": "issued",
                "tenant_label": TENANT,
            })
            bump("fiscal_document")
            for li, (at_uuid, amount, _variant_uuid) in enumerate(realised_treatments, start=1):
                fl_sid = f"FDL{next_flineid:05d}"
                next_flineid += 1
                base = round(amount / 1.21, 2)
                vat = round(amount - base, 2)
                append(conn, "fiscal_document_line", fl_sid, {
                    "document_uuid": fd_uuid,
                    "patient_uuid": p_uuid,
                    "applied_treatment_uuid": at_uuid,
                    "line_number": li,
                    "concept": f"Tratamiento clínico (línea {li})",
                    "amount": str(amount),
                    "base_amount": str(base),
                    "vat_percent": "21",
                    "vat_amount": str(vat),
                    "units": 1,
                    "tenant_label": TENANT,
                })
                bump("fiscal_document_line")

        # ---- Payments (1-3) ----
        for _ in range(rnd.randint(1, 3)):
            pay_sid = f"PAY{next_payid:05d}"
            next_payid += 1
            paid = date.today() - timedelta(days=rnd.randint(0, 900))
            method = rnd.choice([1, 2, 3, 4])
            amount = round(rnd.uniform(20, 300), 2)
            append(conn, "payment", pay_sid, {
                "client_uuid": c_uuid,
                "patient_uuid": p_uuid,
                "user_uuid": rnd.choice(user_uuids),
                "amount": str(amount),
                "paid_on": iso(paid),
                "payment_kind": method,
                "notes": "Pago migrado dental-bridge.",
                "tenant_label": TENANT,
            })
            bump("payment")

    return counts


def main(out: Path) -> None:
    conn = init_db(out)
    write_meta(conn)
    counts = fab(conn)
    finalise(conn, counts)
    conn.close()
    print(f"Wrote {out} — entities:")
    for et, n in sorted(counts.items()):
        print(f"  {et:30s} {n:>6d}")


if __name__ == "__main__":
    out_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/fake_clinica.dpm")
    main(out_path)
