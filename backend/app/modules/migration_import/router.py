"""FastAPI router for the migration_import module.

Eight endpoints behind ``/api/v1/migration-import/``:

- ``POST   /jobs``                  upload, returns the ImportJob row
- ``POST   /jobs/{id}/validate``    decrypt/decompress/verify hash
- ``POST   /jobs/{id}/preview``     entity counts + samples + warnings
- ``POST   /jobs/{id}/execute``     run mappers as a BackgroundTask
- ``GET    /jobs``                  paginated list for the current clinic
- ``GET    /jobs/{id}``             detail (with progress)
- ``GET    /jobs/{id}/warnings``    paginated warnings
- ``POST   /jobs/{id}/binaries``    sync-agent receiver
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Annotated
from uuid import UUID

import aiofiles
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.dependencies import (
    ClinicContext,
    get_clinic_context,
    require_permission,
)
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .binaries.ingest import ingest_binary
from .lifecycle import _staging_root
from .schemas import (
    ExecuteRequest,
    ImportJobResponse,
    PreviewResponse,
    ValidateRequest,
    WarningResponse,
)
from .service import ImportJobService

logger = logging.getLogger(__name__)

router = APIRouter()

# Default 5 GB cap on a DPMF upload. The actual binaries (radiographs,
# PDFs) come through ``/binaries`` one file at a time, so the .dpm file
# itself stays well under this in practice. Configurable via env.
_MAX_UPLOAD_BYTES = getattr(settings, "MIGRATION_MAX_DPMF_BYTES", 5 * 1024 * 1024 * 1024)
_UPLOAD_CHUNK = 1 << 20  # 1 MiB chunks to keep memory bounded


# ---------------------------------------------------------------------------
# POST /jobs — upload a DPMF file
# ---------------------------------------------------------------------------


@router.post(
    "/jobs",
    response_model=ApiResponse[ImportJobResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    file: Annotated[UploadFile, File()],
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.job.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ImportJobResponse]:
    """Stream the upload to disk and return a job row in ``uploaded``."""
    job_id = uuid.uuid4()
    staging_dir = _staging_root() / str(ctx.clinic_id)
    staging_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "dpmf").suffix or ".dpm"
    staged_path = staging_dir / f"{job_id}{extension}"

    written = 0
    try:
        async with aiofiles.open(staged_path, "wb") as out:
            while True:
                chunk = await file.read(_UPLOAD_CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                if written > _MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"DPMF exceeds {_MAX_UPLOAD_BYTES} bytes",
                    )
                await out.write(chunk)
    except HTTPException:
        # 413 — clean up the partial file before re-raising.
        staged_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        staged_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"failed to stage upload: {exc}",
        ) from exc

    job = await ImportJobService.create_job(
        db,
        clinic_id=ctx.clinic_id,
        user_id=ctx.user_id,
        original_filename=file.filename or staged_path.name,
        staged_path=staged_path,
        file_size=written,
    )
    return ApiResponse(data=ImportJobResponse.model_validate(job))


# ---------------------------------------------------------------------------
# POST /jobs/{id}/validate
# ---------------------------------------------------------------------------


@router.post(
    "/jobs/{job_id}/validate",
    response_model=ApiResponse[ImportJobResponse],
)
async def validate_job(
    job_id: UUID,
    request: ValidateRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.job.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ImportJobResponse]:
    job = await _get_job_or_404(db, ctx.clinic_id, job_id)
    job = await ImportJobService.validate(db, job, passphrase=request.passphrase)
    return ApiResponse(data=ImportJobResponse.model_validate(job))


# ---------------------------------------------------------------------------
# POST /jobs/{id}/preview
# ---------------------------------------------------------------------------


@router.post(
    "/jobs/{job_id}/preview",
    response_model=ApiResponse[PreviewResponse],
)
async def preview_job(
    job_id: UUID,
    request: ValidateRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.job.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PreviewResponse]:
    job = await _get_job_or_404(db, ctx.clinic_id, job_id)
    try:
        preview = await ImportJobService.preview(db, job, passphrase=request.passphrase)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ApiResponse(data=preview)


# ---------------------------------------------------------------------------
# POST /jobs/{id}/execute
# ---------------------------------------------------------------------------


@router.post(
    "/jobs/{job_id}/execute",
    response_model=ApiResponse[ImportJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_job(
    job_id: UUID,
    request: ExecuteRequest,
    background_tasks: BackgroundTasks,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.job.execute"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ImportJobResponse]:
    job = await _get_job_or_404(db, ctx.clinic_id, job_id)
    if job.status not in {"validated", "previewing", "completed"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"cannot execute job in status {job.status}",
        )
    background_tasks.add_task(
        ImportJobService.execute_in_background,
        job.id,
        ctx.clinic_id,
        passphrase=request.passphrase,
        import_fiscal_compliance=request.import_fiscal_compliance,
    )
    return ApiResponse(data=ImportJobResponse.model_validate(job))


# ---------------------------------------------------------------------------
# GET /jobs (list)
# ---------------------------------------------------------------------------


@router.get(
    "/jobs",
    response_model=PaginatedApiResponse[ImportJobResponse],
)
async def list_jobs(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.job.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[ImportJobResponse]:
    items, total = await ImportJobService.list_jobs(db, ctx.clinic_id, page, page_size)
    return PaginatedApiResponse(
        data=[ImportJobResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /jobs/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/jobs/{job_id}",
    response_model=ApiResponse[ImportJobResponse],
)
async def get_job(
    job_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.job.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ImportJobResponse]:
    job = await _get_job_or_404(db, ctx.clinic_id, job_id)
    return ApiResponse(data=ImportJobResponse.model_validate(job))


# ---------------------------------------------------------------------------
# GET /jobs/{id}/warnings
# ---------------------------------------------------------------------------


@router.get(
    "/jobs/{job_id}/warnings",
    response_model=PaginatedApiResponse[WarningResponse],
)
async def list_warnings(
    job_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.job.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    severity: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> PaginatedApiResponse[WarningResponse]:
    # Implicit auth check — confirm job belongs to the caller's clinic.
    await _get_job_or_404(db, ctx.clinic_id, job_id)
    items, total = await ImportJobService.list_warnings(
        db, job_id, page, page_size, severity=severity, entity_type=entity_type
    )
    return PaginatedApiResponse(
        data=[WarningResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# POST /jobs/{id}/binaries — sync agent uploads a single binary
# ---------------------------------------------------------------------------


@router.post(
    "/jobs/{job_id}/binaries",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
async def upload_binary(
    job_id: UUID,
    file: Annotated[UploadFile, File()],
    sha256: Annotated[str, Form()],
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("migration_import.binary.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[dict]:
    job = await _get_job_or_404(db, ctx.clinic_id, job_id)
    result = await ingest_binary(db, job=job, file=file, claimed_sha256=sha256)
    return ApiResponse(data=result)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_job_or_404(db: AsyncSession, clinic_id: UUID, job_id: UUID):
    job = await ImportJobService.get_job(db, clinic_id, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return job
