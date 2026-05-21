"""Carve a DPMF file down to N patients + everything that references them.

dental-bridge's `extract` is all-or-nothing per clinic; for fast
iteration on a real Gesdén dataset we want a representative subset
with the full per-patient graph (treatments, phases, budgets,
budget_lines, invoices, invoice_lines, payments, debts, appointments,
documents, alerts, prescriptions, consents…) but only for a sample.

Algorithm:

1. Pick N patient ``canonical_uuid``s at random (deterministic seed).
2. Expand to all ``client_uuid``s linked to those patients via
   ``patient_client_link``.
3. Walk every entity table in two passes:
   - Pass 1 keeps anything that points at a kept patient or client
     directly (``payload.patient_uuid`` / ``payload.client_uuid``).
   - Pass 2 keeps children whose foreign canonical_uuid is now in the
     kept set (``budget_line.budget_uuid``,
     ``applied_treatment_phase.applied_treatment_uuid``,
     ``fiscal_document_line.document_uuid``,
     ``debt_payment_application.debt_uuid`` / ``.payment_uuid``).
4. Always keep clinic-wide rows (centers, professionals, users,
   catalog items, work calendars, appointment recurrences).
5. Rebuild ``_entities`` row counts and recompute the integrity hash
   so the importer's validation passes.

Usage::

    python scripts/subset_dpmf.py <src.dpm> <dst.dpm> --patients 500
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

# Tables whose rows always survive (clinic-wide catalogue / config).
KEEP_ALL_TABLES = {
    "center",
    "professional",
    "user",
    "catalog_item",
    "treatment_catalog_item",
    "treatment_catalog_variant",
    "treatment_phase_template",
    "work_calendar",
    "work_calendar_day",
    "work_calendar_shift",
    "appointment_recurrence",
}


def list_entity_tables(conn: sqlite3.Connection) -> list[str]:
    out = []
    for (name,) in conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' "
        "AND name NOT LIKE '\\_%' ESCAPE '\\' "
        "AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ):
        out.append(name)
    return out


def collect_canonicals(conn: sqlite3.Connection, table: str) -> dict[str, dict]:
    """Read every row into memory keyed by canonical_uuid."""
    rows: dict[str, dict] = {}
    for canonical_uuid, payload_text in conn.execute(
        f'SELECT canonical_uuid, payload FROM "{table}"'
    ):
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError:
            payload = {}
        rows[canonical_uuid] = payload
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("src", type=Path)
    p.add_argument("dst", type=Path)
    p.add_argument("--patients", type=int, default=500)
    p.add_argument("--seed", type=int, default=20260521)
    args = p.parse_args()

    print(f"Copying {args.src} → {args.dst}…")
    shutil.copy2(args.src, args.dst)
    conn = sqlite3.connect(args.dst)
    conn.execute("PRAGMA foreign_keys = OFF")

    # --- 1. Pick the patient sample ----------------------------------------
    all_patients = [
        r[0]
        for r in conn.execute(
            "SELECT canonical_uuid FROM patient ORDER BY canonical_uuid"
        )
    ]
    import random as _r

    rng = _r.Random(args.seed)
    sample = set(rng.sample(all_patients, min(args.patients, len(all_patients))))
    print(f"Selected {len(sample)} patients (of {len(all_patients)})")

    # --- 2. Expand to linked clients --------------------------------------
    clients = set()
    pcl_payloads = collect_canonicals(conn, "patient_client_link")
    for pcl_uuid, payload in pcl_payloads.items():
        if payload.get("patient_uuid") in sample:
            cu = payload.get("client_uuid")
            if cu:
                clients.add(cu)
    print(f"Expanded to {len(clients)} linked clients")

    # The "kept set" is the union of patient + client + every canonical
    # we discover along the way (so children can join on their parents).
    kept: dict[str, set[str]] = {
        "patient": set(sample),
        "client": set(clients),
    }

    # --- 3. First pass: anything referencing a kept patient or client ----
    tables = list_entity_tables(conn)
    print(f"Walking {len(tables)} entity tables…")
    primary_pass_tables = [
        t
        for t in tables
        if t not in KEEP_ALL_TABLES
        and t not in {"patient", "client", "patient_client_link"}
        and t
        not in {
            "applied_treatment_phase",
            "budget_line",
            "fiscal_document_line",
            "debt_payment_application",
        }
    ]
    for table in primary_pass_tables:
        rows = collect_canonicals(conn, table)
        keep_here: set[str] = set()
        for canonical_uuid, payload in rows.items():
            pu = payload.get("patient_uuid")
            cu = payload.get("client_uuid")
            if pu in kept["patient"] or cu in kept["client"]:
                keep_here.add(canonical_uuid)
        kept[table] = keep_here
        print(f"  {table}: kept {len(keep_here)} / {len(rows)}")

    # --- 4. Second pass: children of kept parents -------------------------
    # applied_treatment_phase ← applied_treatment.canonical_uuid
    if "applied_treatment" in kept:
        phase_keep: set[str] = set()
        for canonical_uuid, payload in collect_canonicals(
            conn, "applied_treatment_phase"
        ).items():
            if payload.get("applied_treatment_uuid") in kept["applied_treatment"]:
                phase_keep.add(canonical_uuid)
        kept["applied_treatment_phase"] = phase_keep
        print(f"  applied_treatment_phase: kept {len(phase_keep)}")

    # budget_line ← budget.canonical_uuid
    if "budget" in kept:
        bl_keep: set[str] = set()
        for canonical_uuid, payload in collect_canonicals(conn, "budget_line").items():
            if payload.get("budget_uuid") in kept["budget"]:
                bl_keep.add(canonical_uuid)
        kept["budget_line"] = bl_keep
        print(f"  budget_line: kept {len(bl_keep)}")

    # fiscal_document_line ← fiscal_document.canonical_uuid
    if "fiscal_document" in kept:
        fdl_keep: set[str] = set()
        for canonical_uuid, payload in collect_canonicals(
            conn, "fiscal_document_line"
        ).items():
            if payload.get("document_uuid") in kept["fiscal_document"]:
                fdl_keep.add(canonical_uuid)
        kept["fiscal_document_line"] = fdl_keep
        print(f"  fiscal_document_line: kept {len(fdl_keep)}")

    # debt_payment_application ← debt + payment
    debt_keep = kept.get("debt", set())
    pay_keep = kept.get("payment", set())
    if debt_keep or pay_keep:
        dpa_keep: set[str] = set()
        for canonical_uuid, payload in collect_canonicals(
            conn, "debt_payment_application"
        ).items():
            if (
                payload.get("debt_uuid") in debt_keep
                or payload.get("payment_uuid") in pay_keep
            ):
                dpa_keep.add(canonical_uuid)
        kept["debt_payment_application"] = dpa_keep
        print(f"  debt_payment_application: kept {len(dpa_keep)}")

    # prescription_item ← prescription
    if "prescription" in kept:
        pi_keep: set[str] = set()
        for canonical_uuid, payload in collect_canonicals(
            conn, "prescription_item"
        ).items():
            if payload.get("prescription_uuid") in kept["prescription"]:
                pi_keep.add(canonical_uuid)
        kept["prescription_item"] = pi_keep
        print(f"  prescription_item: kept {len(pi_keep)}")

    # --- 5. Apply deletes -------------------------------------------------
    for table in tables:
        if table in KEEP_ALL_TABLES:
            continue
        if table == "patient":
            placeholders = ",".join("?" * len(sample))
            conn.execute(
                f"DELETE FROM patient WHERE canonical_uuid NOT IN ({placeholders})",
                tuple(sample),
            )
            continue
        if table == "client":
            if clients:
                placeholders = ",".join("?" * len(clients))
                conn.execute(
                    f"DELETE FROM client WHERE canonical_uuid NOT IN ({placeholders})",
                    tuple(clients),
                )
            else:
                conn.execute("DELETE FROM client")
            continue
        if table == "patient_client_link":
            kept_pcl = {
                u
                for u, pay in pcl_payloads.items()
                if pay.get("patient_uuid") in sample
            }
            if kept_pcl:
                placeholders = ",".join("?" * len(kept_pcl))
                conn.execute(
                    f"DELETE FROM patient_client_link WHERE canonical_uuid NOT IN ({placeholders})",
                    tuple(kept_pcl),
                )
            else:
                conn.execute("DELETE FROM patient_client_link")
            continue
        keep_set = kept.get(table, set())
        if keep_set:
            # Chunk the IN clause — SQLite tops out around 999 placeholders.
            keep_list = list(keep_set)
            tmp_table = f"_tmp_keep_{table}"
            conn.execute(f"DROP TABLE IF EXISTS {tmp_table}")
            conn.execute(f"CREATE TEMP TABLE {tmp_table}(uuid TEXT PRIMARY KEY)")
            conn.executemany(
                f"INSERT OR IGNORE INTO {tmp_table}(uuid) VALUES (?)",
                ((u,) for u in keep_list),
            )
            conn.execute(
                f'DELETE FROM "{table}" WHERE canonical_uuid NOT IN '
                f"(SELECT uuid FROM {tmp_table})"
            )
            conn.execute(f"DROP TABLE {tmp_table}")
        else:
            conn.execute(f'DELETE FROM "{table}"')

    # Also prune _files manifest to the kept parents.
    all_kept_canonical: set[str] = set()
    for s in kept.values():
        all_kept_canonical.update(s)
    all_kept_canonical.update(sample)
    all_kept_canonical.update(clients)

    files_before = conn.execute("SELECT COUNT(*) FROM _files").fetchone()[0]
    conn.execute("DROP TABLE IF EXISTS _tmp_kept_canonical")
    conn.execute("CREATE TEMP TABLE _tmp_kept_canonical(uuid TEXT PRIMARY KEY)")
    conn.executemany(
        "INSERT OR IGNORE INTO _tmp_kept_canonical(uuid) VALUES (?)",
        ((u,) for u in all_kept_canonical),
    )
    conn.execute(
        "DELETE FROM _files WHERE parent_canonical_uuid NOT IN "
        "(SELECT uuid FROM _tmp_kept_canonical)"
    )
    conn.execute("DROP TABLE _tmp_kept_canonical")
    files_after = conn.execute("SELECT COUNT(*) FROM _files").fetchone()[0]
    print(f"_files pruned: {files_before} → {files_after}")

    # --- 6. Recompute _entities row counts -------------------------------
    print("Refreshing _entities row counts…")
    for table in tables:
        cnt = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        conn.execute(
            "UPDATE _entities SET row_count = ? WHERE entity_type = ?",
            (cnt, table),
        )
    # Drop any _entities row whose table is now empty AND of type
    # subsetted to nothing — keep them with row_count=0 so the
    # importer's preview still shows the entity.

    conn.commit()

    # --- 7. Recompute integrity hash -------------------------------------
    print("Recomputing integrity hash…")
    hasher = hashlib.sha256()
    for row in conn.execute(
        "SELECT entity_type, row_count, schema_version FROM _entities ORDER BY entity_type"
    ):
        hasher.update(f"_entities|{row[0]}|{row[1]}|{row[2]}\n".encode())
    for table in tables:
        for row in conn.execute(
            f'SELECT canonical_uuid, source_id, source_system, payload, raw_source_data '
            f'FROM "{table}" ORDER BY canonical_uuid'
        ):
            hasher.update(
                f"{table}|{row[0]}|{row[1]}|{row[2]}|{row[3]}|{row[4]}\n".encode()
            )
    for row in conn.execute(
        "SELECT canonical_uuid, parent_entity_type, parent_canonical_uuid, "
        "relative_path, declared_size_bytes, sha256, mime_hint "
        "FROM _files ORDER BY canonical_uuid"
    ):
        hasher.update(("_files|" + "|".join(str(v) for v in row) + "\n").encode())
    for row in conn.execute(
        "SELECT id, entity_type, source_id, severity, code, message, raw_data "
        "FROM _warnings ORDER BY id"
    ):
        hasher.update(("_warnings|" + "|".join(str(v) for v in row) + "\n").encode())
    digest = hasher.hexdigest()
    conn.execute("UPDATE _meta SET value = ? WHERE key = 'integrity_hash'", (digest,))
    conn.commit()

    # --- 8. Vacuum so the file shrinks on disk ---------------------------
    print("VACUUM…")
    conn.execute("VACUUM")
    conn.close()

    size = args.dst.stat().st_size
    print(f"Done. {args.dst} = {size:,} bytes (hash={digest[:16]}…)")


if __name__ == "__main__":
    main()
