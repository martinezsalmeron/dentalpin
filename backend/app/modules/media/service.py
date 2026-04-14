"""Business logic service for media module."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import EventType, event_bus

from .models import Document
from .storage import get_storage_backend
from .validation import get_file_extension


class DocumentService:
    """Service for document operations."""

    @staticmethod
    def generate_storage_path(
        clinic_id: UUID,
        patient_id: UUID,
        original_filename: str,
    ) -> str:
        """Generate unique storage path.

        Format: {clinic_id}/{patient_id}/{YYYY-MM}/{uuid}.{ext}
        """
        now = datetime.utcnow()
        year_month = now.strftime("%Y-%m")
        file_id = uuid4()
        ext = get_file_extension(original_filename)

        if ext:
            return f"{clinic_id}/{patient_id}/{year_month}/{file_id}.{ext}"
        return f"{clinic_id}/{patient_id}/{year_month}/{file_id}"

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        document_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Document], int]:
        """List documents for a patient."""
        page_size = min(max(page_size, 1), 100)
        page = max(page, 1)
        offset = (page - 1) * page_size

        query = select(Document).where(
            Document.clinic_id == clinic_id,
            Document.patient_id == patient_id,
            Document.status == "active",
        )

        if document_type:
            query = query.where(Document.document_type == document_type)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Fetch with uploader
        query = (
            query.options(selectinload(Document.uploader))
            .order_by(Document.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        documents = list(result.scalars().all())

        return documents, total

    @staticmethod
    async def get_document(
        db: AsyncSession,
        clinic_id: UUID,
        document_id: UUID,
    ) -> Document | None:
        """Get document by ID with uploader."""
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.uploader))
            .where(
                Document.id == document_id,
                Document.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_document(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
        user_id: UUID,
        file_data: bytes,
        original_filename: str,
        mime_type: str,
        document_type: str,
        title: str,
        description: str | None = None,
    ) -> Document:
        """Upload and create document record.

        Transaction strategy: file first, then DB.
        Orphan files recoverable; failed DB = no record.
        """
        storage = get_storage_backend()

        # Generate path and store file
        storage_path = DocumentService.generate_storage_path(
            clinic_id, patient_id, original_filename
        )
        await storage.store(file_data, storage_path)

        # Create DB record
        document = Document(
            clinic_id=clinic_id,
            patient_id=patient_id,
            document_type=document_type,
            title=title,
            description=description,
            original_filename=original_filename,
            storage_path=storage_path,
            mime_type=mime_type,
            file_size=len(file_data),
            uploaded_by=user_id,
        )
        db.add(document)
        await db.flush()

        # Publish event for timeline
        event_bus.publish(
            EventType.DOCUMENT_UPLOADED,
            {
                "document_id": str(document.id),
                "clinic_id": str(clinic_id),
                "patient_id": str(patient_id),
                "title": title,
                "document_type": document_type,
            },
        )

        # Reload with uploader relationship
        await db.refresh(document, ["uploader"])

        return document

    @staticmethod
    async def update_document(
        db: AsyncSession,
        document: Document,
        data: dict,
    ) -> Document:
        """Update document metadata."""
        for key, value in data.items():
            if value is not None:
                setattr(document, key, value)

        await db.flush()
        await db.refresh(document, ["uploader"])
        return document

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        document: Document,
    ) -> None:
        """Soft delete document (set status=archived)."""
        document.status = "archived"
        await db.flush()

        event_bus.publish(
            EventType.DOCUMENT_DELETED,
            {
                "document_id": str(document.id),
                "clinic_id": str(document.clinic_id),
                "patient_id": str(document.patient_id),
            },
        )

    @staticmethod
    async def download_document(document: Document) -> bytes:
        """Get file content for download."""
        storage = get_storage_backend()
        return await storage.retrieve(document.storage_path)

    @staticmethod
    async def archive_patient_documents(
        db: AsyncSession,
        clinic_id: UUID,
        patient_id: UUID,
    ) -> int:
        """Archive all documents for a patient (cascade soft-delete).

        Returns count of archived documents.
        """
        result = await db.execute(
            select(Document).where(
                Document.clinic_id == clinic_id,
                Document.patient_id == patient_id,
                Document.status == "active",
            )
        )
        documents = list(result.scalars().all())

        for doc in documents:
            doc.status = "archived"

        await db.flush()
        return len(documents)
