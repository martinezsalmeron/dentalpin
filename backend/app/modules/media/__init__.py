"""Media module - document and file management."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType
from app.core.plugins import BaseModule

from .models import Document, MediaAttachment
from .router import router
from .service import DocumentService


class MediaModule(BaseModule):
    """Media module providing document management."""

    manifest = {
        "name": "media",
        "version": "0.2.0",
        "summary": "Patient documents, photos, X-rays + polymorphic attachments.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["patients"],
        "installable": True,
        "auto_install": True,
        "removable": False,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["*"],
            "hygienist": [
                "documents.read",
                "attachments.read",
                "attachments.write",
            ],
            "assistant": ["*"],
            "receptionist": ["*"],
        },
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def get_models(self) -> list:
        return [Document, MediaAttachment]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return [
            "documents.read",
            "documents.write",
            "attachments.read",
            "attachments.write",
        ]

    def get_event_handlers(self) -> dict[str, Any]:
        """Register event handlers."""
        return {
            EventType.PATIENT_ARCHIVED: self._on_patient_archived,
        }

    async def _on_patient_archived(self, db: AsyncSession, data: dict) -> None:
        """Cascade soft-delete documents when patient is archived."""
        from uuid import UUID

        patient_id = UUID(data["patient_id"])
        clinic_id = UUID(data["clinic_id"])

        await DocumentService.archive_patient_documents(db, clinic_id, patient_id)
