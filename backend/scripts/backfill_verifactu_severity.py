"""One-shot backfill of ``Invoice.compliance_data['ES'].severity``.

Why this exists: the severity field was added in the badge-and-filter
sprint after a number of invoices already had ``compliance_data['ES']``
populated by the original hook. Without backfill, those rows would not
match the new ``compliance_severity`` filter and would render no badge
in the list until they are reissued — confusing UX.

What it does: for every invoice with ``compliance_data['ES']`` but no
``severity`` key, look up the latest ``VerifactuRecord`` for that
invoice and compute severity from its ``state`` + ``aeat_codigo_error``.
Idempotent — rows that already carry a severity are left alone.

Usage::

    docker-compose exec backend python backend/scripts/backfill_verifactu_severity.py

Run once after deploying the badge sprint. Can be re-run safely.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow running the script directly via `python backend/scripts/...`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

# Force SQLAlchemy to resolve every cross-module relationship by
# loading all module models the same way the app does at startup.
from app.core.plugins.loader import load_modules  # noqa: E402
from app.database import async_session_maker  # noqa: E402
from app.main import app as _app  # noqa: E402

load_modules(_app)

from app.modules.billing.models import Invoice  # noqa: E402
from app.modules.verifactu.models import VerifactuRecord  # noqa: E402
from app.modules.verifactu.services.severity import severity_for  # noqa: E402


async def main() -> int:
    updated = 0
    skipped = 0
    no_record = 0

    async with async_session_maker() as db:
        invs_q = await db.execute(select(Invoice).where(Invoice.compliance_data.is_not(None)))
        invoices = list(invs_q.scalars())

        for inv in invoices:
            cd = inv.compliance_data or {}
            es = cd.get("ES") or {}
            if "severity" in es and es["severity"]:
                skipped += 1
                continue

            rec_q = await db.execute(
                select(VerifactuRecord)
                .where(VerifactuRecord.invoice_id == inv.id)
                .order_by(VerifactuRecord.created_at.desc())
                .limit(1)
            )
            record = rec_q.scalar_one_or_none()
            if record is None:
                no_record += 1
                continue

            severity = severity_for(record.state, record.aeat_codigo_error)
            new_es = dict(es)
            new_es["severity"] = severity
            new_es.setdefault("state", record.state)
            new_es.setdefault("error_code", record.aeat_codigo_error)
            new_es.setdefault("error_message", record.aeat_descripcion_error)
            new_cd = dict(cd)
            new_cd["ES"] = new_es
            inv.compliance_data = new_cd
            updated += 1

        await db.commit()

    print(
        f"backfill_verifactu_severity: updated={updated} "
        f"skipped_already_set={skipped} skipped_no_record={no_record}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
