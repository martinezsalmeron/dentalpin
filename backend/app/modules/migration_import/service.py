"""ImportJobService — orchestrates upload, validate, preview, execute.

The state machine:

    uploaded → validating → validated → previewing → executing → completed
                                                              \\→ failed

Validate, preview and execute all run as BackgroundTasks so the HTTP
endpoints return immediately. Their progress + errors land back in
the ImportJob row, which the UI polls.

Idempotency for ``execute`` is delegated to the mappers via the
:class:`EntityMapping` table — re-running execute on a job that already
completed is a no-op for rows already mapped.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins import module_registry
from app.database import async_session_maker

from .dpmf import DpmfHandle, open_dpmf
from .dpmf.crypto import DpmeError
from .dpmf.reader import DpmfFormatError
from .events import (
    publish_entity_persisted,
    publish_job_completed,
    publish_job_failed,
    publish_job_started,
)
from .mappers import FALLBACK_MAPPER, MAPPERS, MapperContext, MappingResolver
from .models import FileStaging, ImportJob, ImportWarning
from .schemas import (
    EntityPreview,
    FilesManifestSummary,
    PreviewResponse,
    PreviewSample,
    WarningView,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Refuse files whose major exceeds this. v0.1 supports 0.x only.
_SUPPORTED_MAJOR = 0
# Sample rows per entity in the preview response.
_PREVIEW_SAMPLE_SIZE = 5
# Commit every N entities so a restart can resume close to where it
# stopped. Mappers are idempotent so larger batches just waste rework
# on resume, not consistency.
_COMMIT_BATCH = 500


class ImportJobService:
    """All business logic for the DPMF importer."""

    # ---- create / upload --------------------------------------------------

    @staticmethod
    async def create_job(
        db: AsyncSession,
        *,
        clinic_id: UUID,
        user_id: UUID,
        original_filename: str,
        staged_path: Path,
        file_size: int,
    ) -> ImportJob:
        job = ImportJob(
            clinic_id=clinic_id,
            created_by=user_id,
            status="uploaded",
            original_filename=original_filename,
            file_path=str(staged_path),
            file_size=file_size,
        )
        db.add(job)
        await db.flush()
        return job

    @staticmethod
    async def get_job(db: AsyncSession, clinic_id: UUID, job_id: UUID) -> ImportJob | None:
        result = await db.execute(
            select(ImportJob).where(ImportJob.id == job_id, ImportJob.clinic_id == clinic_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_jobs(
        db: AsyncSession, clinic_id: UUID, page: int, page_size: int
    ) -> tuple[list[ImportJob], int]:
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size
        base = select(ImportJob).where(ImportJob.clinic_id == clinic_id)
        total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        rows = await db.execute(
            base.order_by(ImportJob.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(rows.scalars().all()), total

    # ---- validate ---------------------------------------------------------

    @staticmethod
    async def validate(db: AsyncSession, job: ImportJob, *, passphrase: str | None) -> ImportJob:
        """Open the file (decrypt/decompress), populate `_meta` columns,
        recompute and compare the integrity hash."""
        job.status = "validating"
        await db.flush()

        try:
            with open_dpmf(Path(job.file_path), passphrase=passphrase) as handle:
                meta = handle.meta
                ImportJobService._fill_meta(job, meta)
                ImportJobService._check_format_version(meta)
                computed = handle.recompute_integrity_hash()
                job.integrity_hash_computed = computed
                declared = handle.declared_integrity_hash()
                if declared and declared != computed:
                    raise DpmfFormatError(
                        f"integrity hash mismatch: declared={declared} computed={computed}"
                    )
                # Populate total_entities for progress UI.
                counts = handle.entity_counts()
                job.total_entities = sum(counts.values())
                job.status = "validated"
        except (DpmeError, DpmfFormatError) as exc:
            job.status = "failed"
            job.error = str(exc)
            logger.warning("DPMF validation failed for job %s: %s", job.id, exc)
        except Exception as exc:
            job.status = "failed"
            job.error = f"unexpected validation error: {exc}"
            logger.exception("Unexpected DPMF validation error for job %s", job.id)
        await db.flush()
        return job

    @staticmethod
    def _fill_meta(job: ImportJob, meta: dict[str, str]) -> None:
        job.source_system = meta.get("source_system")
        job.source_adapter_version = meta.get("source_adapter_version")
        job.exporter_tool = meta.get("exporter_tool")
        job.exporter_version = meta.get("exporter_version")
        job.format_version = meta.get("format_version")
        job.tenant_label = meta.get("tenant_label")
        job.integrity_hash_declared = meta.get("integrity_hash")

    @staticmethod
    def _check_format_version(meta: dict[str, str]) -> None:
        version = meta.get("format_version", "")
        try:
            major = int(version.split(".", 1)[0])
        except (ValueError, IndexError) as exc:
            raise DpmfFormatError(f"missing or invalid format_version: {version!r}") from exc
        if major > _SUPPORTED_MAJOR:
            raise DpmfFormatError(
                f"DPMF format_version {version} not supported (supports {_SUPPORTED_MAJOR}.x)"
            )

    # ---- preview ----------------------------------------------------------

    @staticmethod
    async def preview(
        db: AsyncSession, job: ImportJob, *, passphrase: str | None
    ) -> PreviewResponse:
        """Read entity counts, sample rows, warnings, _files summary.

        Reads the DPMF in read-only mode; no DentalPin rows are created.
        """
        if job.status not in {"validated", "previewing", "completed"}:
            raise ValueError(f"job {job.id} cannot be previewed from status {job.status}")
        job.status = "previewing"
        await db.flush()

        with open_dpmf(Path(job.file_path), passphrase=passphrase) as handle:
            previews = ImportJobService._build_entity_previews(handle)
            warnings = ImportJobService._build_warnings(handle)
            files = ImportJobService._build_files_summary(handle)
            verifactu_detected = _detect_verifactu_data(handle)

        verifactu_installed = module_registry.is_loaded("verifactu")

        from .schemas import ImportJobResponse

        return PreviewResponse(
            job=ImportJobResponse.model_validate(job),
            entities=previews,
            warnings=warnings,
            files=files,
            verifactu_data_detected=verifactu_detected,
            verifactu_module_installed=verifactu_installed,
        )

    @staticmethod
    def _build_entity_previews(handle: DpmfHandle) -> list[EntityPreview]:
        previews: list[EntityPreview] = []
        for entity_type, count in handle.entity_counts().items():
            samples: list[PreviewSample] = []
            for i, row in enumerate(handle.entity_iter(entity_type)):
                if i >= _PREVIEW_SAMPLE_SIZE:
                    break
                canonical_uuid, source_id, _src_system, payload_json, _raw, _ts = row
                try:
                    payload = json.loads(payload_json)
                except json.JSONDecodeError:
                    payload = {"_decode_error": True}
                samples.append(
                    PreviewSample(
                        canonical_uuid=canonical_uuid,
                        source_id=source_id,
                        payload=payload,
                    )
                )
            previews.append(
                EntityPreview(entity_type=entity_type, declared_count=count, samples=samples)
            )
        return previews

    @staticmethod
    def _build_warnings(handle: DpmfHandle) -> list[WarningView]:
        return [
            WarningView(
                severity=row[2],
                code=row[3],
                message=row[4],
                entity_type=row[0],
                source_id=row[1],
            )
            for row in handle.warnings_iter()
        ]

    @staticmethod
    def _build_files_summary(handle: DpmfHandle) -> FilesManifestSummary:
        total = 0
        with_sha = 0
        for row in handle.files_iter():
            total += 1
            if row[5]:
                with_sha += 1
        return FilesManifestSummary(
            total=total, with_sha256=with_sha, without_sha256=total - with_sha
        )

    # ---- execute ----------------------------------------------------------

    @staticmethod
    async def execute_in_background(
        job_id: UUID,
        clinic_id: UUID,
        *,
        passphrase: str | None,
        import_fiscal_compliance: bool,
    ) -> None:
        """Top-level entry point for the BackgroundTask.

        Owns its own DB session so the original request handler's
        session can return immediately. Errors set ``status='failed'``
        and publish ``migration.job.failed`` — they never bubble to the
        client (we are detached from the request).
        """
        async with async_session_maker() as session:
            try:
                job = await ImportJobService.get_job_unscoped(session, job_id)
                if job is None:
                    logger.error("execute: job %s missing", job_id)
                    return
                if job.status not in {"validated", "previewing", "completed", "executing"}:
                    logger.error("execute: job %s in status %s — refusing", job.id, job.status)
                    return
                if job.clinic_id != clinic_id:
                    logger.error(
                        "execute: clinic mismatch job=%s expected=%s actual=%s",
                        job.id,
                        clinic_id,
                        job.clinic_id,
                    )
                    return

                job.status = "executing"
                job.started_at = datetime.now(UTC)
                job.import_fiscal_compliance = import_fiscal_compliance
                job.error = None
                await session.commit()

                publish_job_started(job.id, job.clinic_id)
                await ImportJobService._run_pipeline(session, job, passphrase=passphrase)

                job.status = "completed"
                job.completed_at = datetime.now(UTC)
                await session.commit()
                warnings_count = (
                    await session.execute(
                        select(func.count()).select_from(
                            select(ImportWarning).where(ImportWarning.job_id == job.id).subquery()
                        )
                    )
                ).scalar() or 0
                publish_job_completed(
                    job.id, job.clinic_id, job.total_entities, int(warnings_count)
                )
            except Exception as exc:
                await session.rollback()
                logger.exception("execute pipeline crashed for job %s", job_id)
                async with async_session_maker() as failure_session:
                    job = await ImportJobService.get_job_unscoped(failure_session, job_id)
                    if job is not None:
                        job.status = "failed"
                        job.error = str(exc)
                        await failure_session.commit()
                        publish_job_failed(job.id, job.clinic_id, str(exc))

    @staticmethod
    async def get_job_unscoped(db: AsyncSession, job_id: UUID) -> ImportJob | None:
        result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def _run_pipeline(db: AsyncSession, job: ImportJob, *, passphrase: str | None) -> None:
        """Walk the DPMF in topological order, dispatch to mappers."""
        from .dpmf.iter import ordered_entity_types

        resolver = MappingResolver(db=db, clinic_id=job.clinic_id, job_id=job.id)
        ctx = MapperContext(
            db=db,
            clinic_id=job.clinic_id,
            job_id=job.id,
            resolver=resolver,
            import_fiscal_compliance=job.import_fiscal_compliance,
        )

        with open_dpmf(Path(job.file_path), passphrase=passphrase) as handle:
            entity_types = ordered_entity_types(list(handle.entity_counts().keys()))

            for entity_type in entity_types:
                mapper = MAPPERS.get(entity_type, FALLBACK_MAPPER)
                processed_in_batch = 0
                for row in handle.entity_iter(entity_type):
                    canonical_uuid, source_id, source_system, payload_json, raw_json, _ts = row
                    try:
                        payload = json.loads(payload_json)
                        raw = json.loads(raw_json)
                    except json.JSONDecodeError as exc:
                        await ImportJobService._record_warning(
                            db,
                            job.id,
                            entity_type,
                            source_id,
                            severity="error",
                            code="payload.decode_error",
                            message=f"JSON decode failed: {exc}",
                        )
                        continue

                    try:
                        await mapper.apply(
                            ctx,
                            entity_type=entity_type,
                            payload=payload,
                            raw=raw,
                            canonical_uuid=canonical_uuid,
                            source_id=source_id,
                            source_system=source_system,
                        )
                        publish_entity_persisted(job.id, entity_type)
                    except Exception as exc:
                        # One entity blowing up does not fail the whole job —
                        # we surface it as a warning and continue. The op
                        # gets a single "X warnings" badge to act on.
                        logger.warning(
                            "mapper %s failed for %s/%s: %s",
                            mapper.__class__.__name__,
                            entity_type,
                            source_id,
                            exc,
                        )
                        await ImportJobService._record_warning(
                            db,
                            job.id,
                            entity_type,
                            source_id,
                            severity="error",
                            code="mapper.failed",
                            message=str(exc),
                        )

                    processed_in_batch += 1
                    if processed_in_batch >= _COMMIT_BATCH:
                        job.last_checkpoint = {
                            "entity_type": entity_type,
                            "after_canonical_uuid": canonical_uuid,
                        }
                        await db.commit()
                        processed_in_batch = 0
                # End-of-entity commit.
                await db.commit()

            # Ingest the DPMF's own _files manifest into our staging table.
            # The document mapper already created one staging row per
            # PatientDocument entity; the manifest provides the canonical
            # set of files the sync agent will upload. We persist every
            # row from _files so the sync agent can match by sha256 even
            # for files whose parent we have not mapped yet.
            await ImportJobService._persist_files_manifest(db, job, handle)
            # Ingest the DPMF's own _warnings into our audit log so the
            # operator sees the same issues the extractor surfaced.
            await ImportJobService._persist_dpmf_warnings(db, job, handle)
            await db.commit()

    @staticmethod
    async def _persist_files_manifest(db: AsyncSession, job: ImportJob, handle: DpmfHandle) -> None:
        for row in handle.files_iter():
            canonical_uuid, parent_type, parent_uuid, rel_path, size, sha, mime = row
            # Skip if we already have it (idempotent re-run).
            existing = await db.execute(
                select(FileStaging).where(
                    FileStaging.job_id == job.id,
                    FileStaging.canonical_uuid == canonical_uuid,
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            staging = FileStaging(
                clinic_id=job.clinic_id,
                job_id=job.id,
                canonical_uuid=canonical_uuid,
                parent_entity_type=parent_type,
                parent_canonical_uuid=parent_uuid,
                relative_path=rel_path,
                declared_size_bytes=size,
                sha256=sha,
                mime_hint=mime,
                status="pending" if sha else "missing",
            )
            db.add(staging)
            if not sha:
                await ImportJobService._record_warning(
                    db,
                    job.id,
                    parent_type,
                    canonical_uuid,
                    severity="warn",
                    code="file.sha256_missing",
                    message=f"file {rel_path} has no sha256 — cannot be matched",
                )

    @staticmethod
    async def _persist_dpmf_warnings(db: AsyncSession, job: ImportJob, handle: DpmfHandle) -> None:
        for row in handle.warnings_iter():
            entity_type, source_id, severity, code, message, raw_data = row
            raw = None
            if raw_data:
                try:
                    raw = json.loads(raw_data)
                except json.JSONDecodeError:
                    raw = {"_decode_error": True, "raw": raw_data}
            db.add(
                ImportWarning(
                    job_id=job.id,
                    entity_type=entity_type,
                    source_id=source_id,
                    severity=severity,
                    code=f"dpmf.{code}",
                    message=message,
                    raw_data=raw,
                )
            )

    @staticmethod
    async def _record_warning(
        db: AsyncSession,
        job_id: UUID,
        entity_type: str | None,
        source_id: str | None,
        *,
        severity: str,
        code: str,
        message: str,
    ) -> None:
        db.add(
            ImportWarning(
                job_id=job_id,
                entity_type=entity_type,
                source_id=source_id,
                severity=severity,
                code=code,
                message=message,
            )
        )

    # ---- warnings ---------------------------------------------------------

    @staticmethod
    async def list_warnings(
        db: AsyncSession,
        job_id: UUID,
        page: int,
        page_size: int,
        *,
        severity: str | None = None,
        entity_type: str | None = None,
    ) -> tuple[list[ImportWarning], int]:
        page_size = min(max(page_size, 1), 200)
        page = max(page, 1)
        offset = (page - 1) * page_size
        base = select(ImportWarning).where(ImportWarning.job_id == job_id)
        if severity:
            base = base.where(ImportWarning.severity == severity)
        if entity_type:
            base = base.where(ImportWarning.entity_type == entity_type)
        total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
        rows = await db.execute(
            base.order_by(ImportWarning.created_at.asc()).offset(offset).limit(page_size)
        )
        return list(rows.scalars().all()), total


def _detect_verifactu_data(handle: DpmfHandle) -> bool:
    """Scan fiscal_document payloads for Spanish legal hash fields."""
    if "fiscal_document" not in handle.entity_counts():
        return False
    for row in handle.entity_iter("fiscal_document"):
        _uuid, _src, _sys, payload_json, _raw, _ts = row
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            continue
        for key in ("legal_hash", "hash", "hash_control", "atcud", "qr_code"):
            if payload.get(key):
                return True
    return False
