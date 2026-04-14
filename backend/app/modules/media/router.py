"""FastAPI router for media module."""

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db
from app.modules.clinical.service import PatientService

from .schemas import DocumentResponse, DocumentUpdate
from .service import DocumentService
from .validation import (
    DOCUMENT_TYPES,
    validate_document_type,
    validate_file_size,
    validate_mime_type,
)

router = APIRouter()


@router.post(
    "/patients/{patient_id}/documents",
    response_model=ApiResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    patient_id: UUID,
    file: Annotated[UploadFile, File()],
    document_type: Annotated[str, Form()],
    title: Annotated[str, Form(min_length=1, max_length=255)],
    description: Annotated[str | None, Form(max_length=2000)] = None,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)] = None,
    _: Annotated[None, Depends(require_permission("media.documents.write"))] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> ApiResponse[DocumentResponse]:
    """Upload a document for a patient."""
    # Validate patient exists and belongs to clinic
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Validate file
    validate_document_type(document_type)
    validate_file_size(file)
    mime_type = validate_mime_type(file)

    # Read file content
    file_data = await file.read()

    # Create document
    document = await DocumentService.create_document(
        db=db,
        clinic_id=ctx.clinic_id,
        patient_id=patient_id,
        user_id=ctx.user_id,
        file_data=file_data,
        original_filename=file.filename or "document",
        mime_type=mime_type,
        document_type=document_type,
        title=title,
        description=description,
    )

    return ApiResponse(data=DocumentResponse.model_validate(document))


@router.get(
    "/patients/{patient_id}/documents",
    response_model=PaginatedApiResponse[DocumentResponse],
)
async def list_patient_documents(
    patient_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("media.documents.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    document_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[DocumentResponse]:
    """List documents for a patient."""
    # Validate patient exists
    patient = await PatientService.get_patient(db, ctx.clinic_id, patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Validate document_type if provided
    if document_type and document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Allowed: {', '.join(DOCUMENT_TYPES)}",
        )

    documents, total = await DocumentService.list_documents(
        db=db,
        clinic_id=ctx.clinic_id,
        patient_id=patient_id,
        document_type=document_type,
        page=page,
        page_size=page_size,
    )

    return PaginatedApiResponse(
        data=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/documents/{document_id}",
    response_model=ApiResponse[DocumentResponse],
)
async def get_document(
    document_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("media.documents.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[DocumentResponse]:
    """Get document metadata by ID."""
    document = await DocumentService.get_document(db, ctx.clinic_id, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return ApiResponse(data=DocumentResponse.model_validate(document))


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("media.documents.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Download document file."""
    document = await DocumentService.get_document(db, ctx.clinic_id, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    content = await DocumentService.download_document(document)

    return Response(
        content=content,
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.original_filename}"',
            "Content-Length": str(document.file_size),
        },
    )


@router.put(
    "/documents/{document_id}",
    response_model=ApiResponse[DocumentResponse],
)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("media.documents.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[DocumentResponse]:
    """Update document metadata."""
    document = await DocumentService.get_document(db, ctx.clinic_id, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    updated = await DocumentService.update_document(
        db, document, data.model_dump(exclude_unset=True)
    )

    return ApiResponse(data=DocumentResponse.model_validate(updated))


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("media.documents.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft delete a document."""
    document = await DocumentService.get_document(db, ctx.clinic_id, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    await DocumentService.delete_document(db, document)
