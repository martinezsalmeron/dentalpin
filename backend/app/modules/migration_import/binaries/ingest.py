"""Receiver for the sync-agent upload flow.

The external agent (lives in dental-bridge) walks the clinic's image
root, computes sha256 for each file, and POSTs every binary to
``/api/v1/migration-import/jobs/{id}/binaries`` along with the sha256
in a form field. We:

1. Read the uploaded body and verify its sha256 matches the claim
   (the agent could be buggy or compromised — never trust the form).
2. Look up the :class:`FileStaging` row by ``(job_id, sha256, status=pending)``.
3. Resolve the owning patient via :class:`EntityMapping`.
4. Hand off to :class:`media.DocumentService.create_document` so the
   bytes live in the storage backend, get a thumbnail, etc.
5. Flip ``FileStaging.status`` to ``received`` and store the document id.

Returning a 404 is the agent's signal to retry later (e.g. the
``patient_document`` mapping hadn't been written yet when the binary
arrived). The agent is expected to back off + retry.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..events import publish_binary_resolved
from ..mappers.document import DOCUMENT_ENTITY_TYPE
from ..models import EntityMapping, FileStaging, ImportJob

logger = logging.getLogger(__name__)


async def ingest_binary(
    db: AsyncSession,
    *,
    job: ImportJob,
    file: UploadFile,
    claimed_sha256: str,
) -> dict[str, Any]:
    """Receive one binary from the sync agent. See module docstring."""
    body = await file.read()
    actual_sha = hashlib.sha256(body).hexdigest()
    if actual_sha != claimed_sha256.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"sha256 mismatch: claimed={claimed_sha256} actual={actual_sha}",
        )

    staging = await _find_staging(db, job_id=job.id, sha256=actual_sha)
    if staging is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no FileStaging row for sha256={actual_sha} in job {job.id}",
        )
    if staging.status == "received":
        return {
            "staging_id": str(staging.id),
            "document_id": str(staging.resolved_document_id),
            "status": "already_received",
        }

    patient_id = await _resolve_patient_for_staging(db, staging=staging)
    if patient_id is None:
        # Agent should retry — the patient_document mapping likely
        # hasn't been written yet (execute pipeline still running).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="parent patient not yet mapped — retry once execute completes",
        )

    # Late import keeps the module loadable when media isn't installed
    # (e.g. uninstall test of media; though we depend on it so this is
    # mostly defensive). Mime/document_type come from the staging hint.
    from app.modules.media.service import DocumentService

    mime = staging.mime_hint or "application/octet-stream"
    title = staging.relative_path.rsplit("/", 1)[-1] or "documento importado"

    document = await DocumentService.create_document(
        db=db,
        clinic_id=staging.clinic_id,
        patient_id=patient_id,
        user_id=job.created_by,
        file_data=body,
        original_filename=title,
        mime_type=mime,
        document_type="imported",
        title=title,
        description=f"Importado dental-bridge (job {job.id})",
    )

    staging.status = "received"
    staging.resolved_document_id = document.id
    from datetime import UTC, datetime

    staging.received_at = datetime.now(UTC)
    await db.flush()

    publish_binary_resolved(job.id, staging.id, document.id)

    return {
        "staging_id": str(staging.id),
        "document_id": str(document.id),
        "status": "received",
    }


async def _find_staging(db: AsyncSession, *, job_id: Any, sha256: str) -> FileStaging | None:
    result = await db.execute(
        select(FileStaging).where(
            FileStaging.job_id == job_id,
            FileStaging.sha256 == sha256,
        )
    )
    return result.scalar_one_or_none()


async def _resolve_patient_for_staging(db: AsyncSession, *, staging: FileStaging) -> Any | None:
    """Walk the parent chain to find the owning patient_id.

    Today only ``patient_document`` parents resolve through the
    document mapper, which writes the entity mapping with
    ``dentalpin_table='patients'`` (and ``dentalpin_id=<patient.id>``).
    Other parent entity types (consent, prescription, ...) need their
    own mappers + this resolver branch.
    """
    if staging.parent_entity_type != DOCUMENT_ENTITY_TYPE:
        return None
    result = await db.execute(
        select(EntityMapping.dentalpin_id).where(
            EntityMapping.clinic_id == staging.clinic_id,
            EntityMapping.entity_type == DOCUMENT_ENTITY_TYPE,
            EntityMapping.source_canonical_uuid == staging.parent_canonical_uuid,
        )
    )
    return result.scalar_one_or_none()
