"""Media module - document and file management."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.core.events import EventType
from app.core.plugins import BaseModule
from app.database import async_session_maker

from .models import Document, MediaAttachment
from .router import router
from .service import DocumentService

logger = logging.getLogger(__name__)


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

    async def _on_patient_archived(self, data: dict) -> None:
        """Cascade soft-archive of a patient's documents when they are
        archived.

        The event bus calls handlers as ``handler(data)`` and publishes
        before the request commits, so this opens its own session and
        commits independently (same pattern as the recalls handler).
        """
        patient_id = data.get("patient_id")
        clinic_id = data.get("clinic_id")
        if not patient_id or not clinic_id:
            logger.error(
                "media._on_patient_archived: missing patient_id/clinic_id in payload: %r",
                data,
            )
            return

        async with async_session_maker() as db:
            try:
                await DocumentService.archive_patient_documents(
                    db, UUID(str(clinic_id)), UUID(str(patient_id))
                )
                await db.commit()
            except Exception as exc:
                logger.error("media._on_patient_archived failed: %s", exc, exc_info=True)
                await db.rollback()
