"""Copilot module — conversational AI agent over DentalPin (issue #81).

A thin *surface* over the core agentic engine (``app/core/agents`` +
``app/core/llm``). Consumes tools through the global registry only;
never imports another module's service, so it keeps ``depends = []`` and
stays cleanly removable. Per-user RBAC parity: the agent can never see
or do anything the calling user couldn't through the UI.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import CopilotConversation, CopilotMessage, CopilotSettings
from .router import router


class CopilotModule(BaseModule):
    manifest = {
        "name": "copilot",
        "version": "0.1.0",
        "summary": "Conversational AI agent over DentalPin, scoped to the caller's permissions.",
        "author": "DentalPin Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": [],
        "installable": True,
        "auto_install": False,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["chat", "history.read"],
            "hygienist": ["chat", "history.read"],
            "assistant": ["chat", "history.read"],
            "receptionist": ["chat", "history.read"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.copilot",
                    "icon": "i-lucide-sparkles",
                    "to": "/copilot",
                    "permission": "copilot.chat",
                    "order": 90,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [CopilotConversation, CopilotMessage, CopilotSettings]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        # Registry namespaces → copilot.chat, copilot.history.read, etc.
        return ["chat", "history.read", "history.read_all", "supervise", "configure"]

    def get_tools(self) -> list:
        # Copilot consumes tools; it exposes none of its own.
        return []
