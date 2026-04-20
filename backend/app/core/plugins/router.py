"""HTTP endpoints for module management.

Mirror of the CLI, exposed so UI clients can trigger the same state
transitions. The heavy lifting happens at the next backend restart —
every mutating endpoint responds ``202 Accepted`` with a "restart
required" message and the list of modules that would be touched.

Routes are mounted at ``/api/v1/modules``.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import (
    ClinicContext,
    get_clinic_context,
    require_permission,
)
from app.core.auth.permissions import has_permission
from app.core.schemas import ApiResponse
from app.database import get_db

from .service import ModuleOperationError, ModuleService
from .state import ModuleState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/modules", tags=["modules"])


# --- Read endpoints ------------------------------------------------------


@router.get("")
async def list_modules(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("admin.clinic.read"))],
) -> ApiResponse[list[dict[str, Any]]]:
    svc = ModuleService(db)
    infos = await svc.list_modules()
    return ApiResponse(data=[info.to_dict() for info in infos])


@router.get("/{name}")
async def get_module(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("admin.clinic.read"))],
) -> ApiResponse[dict[str, Any]]:
    svc = ModuleService(db)
    info = await svc.get_info(name)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Module not found: {name}")
    return ApiResponse(data=info.to_dict())


@router.get("/-/status")
async def module_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("admin.clinic.read"))],
) -> ApiResponse[dict[str, Any]]:
    svc = ModuleService(db)
    return ApiResponse(data=await svc.status())


@router.get("/-/active")
async def active_modules(
    db: Annotated[AsyncSession, Depends(get_db)],
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
) -> ApiResponse[list[dict[str, Any]]]:
    """Modules in ``installed`` state + nav items visible to the caller.

    This is the frontend's source of truth for the sidebar. Every
    authenticated user may read it; navigation entries are filtered by
    the caller's role-based permissions so the response is already
    tailored to what the UI should render.
    """
    svc = ModuleService(db)
    active: list[dict[str, Any]] = []

    for info in await svc.list_modules():
        if info.state != ModuleState.INSTALLED:
            continue

        module = svc.discovered()
        manifest = next((m.get_manifest() for m in module if m.name == info.name), None)
        if manifest is None:
            continue

        nav = list(manifest.frontend.get("navigation") or [])
        filtered_nav = [item for item in nav if _nav_visible(item, ctx.role)]

        active.append(
            {
                "name": manifest.name,
                "version": manifest.version,
                "category": manifest.category.value,
                "summary": manifest.summary,
                "navigation": filtered_nav,
                "permissions": [
                    f"{manifest.name}.{perm}"
                    for perm in next(
                        (m.get_permissions() for m in module if m.name == info.name),
                        [],
                    )
                ],
            }
        )

    return ApiResponse(data=active)


def _nav_visible(item: dict[str, Any], role: str) -> bool:
    perm = item.get("permission")
    if not perm:
        return True
    return has_permission(role, perm)


@router.get("/-/doctor")
async def module_doctor(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("admin.clinic.read"))],
) -> ApiResponse[dict[str, Any]]:
    svc = ModuleService(db)
    return ApiResponse(data=(await svc.doctor()).to_dict())


# --- Mutating endpoints --------------------------------------------------


@router.post("/{name}/install", status_code=status.HTTP_202_ACCEPTED)
async def install_module(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
    force: bool = False,
) -> ApiResponse[dict[str, Any]]:
    svc = ModuleService(db)
    try:
        scheduled = await svc.install(name, force=force)
    except ModuleOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(
        data={"scheduled": scheduled, "requires_restart": bool(scheduled)},
        message="Restart required to apply.",
    )


@router.post("/{name}/uninstall", status_code=status.HTTP_202_ACCEPTED)
async def uninstall_module(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
    force: bool = False,
) -> ApiResponse[dict[str, Any]]:
    svc = ModuleService(db)
    try:
        await svc.uninstall(name, force=force)
    except ModuleOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(
        data={"scheduled": [name], "requires_restart": True},
        message="Restart required to apply. A data backup will be created before removal.",
    )


@router.post("/{name}/upgrade", status_code=status.HTTP_202_ACCEPTED)
async def upgrade_module(
    name: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
) -> ApiResponse[dict[str, Any]]:
    svc = ModuleService(db)
    try:
        changed = await svc.upgrade(name)
    except ModuleOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse(
        data={"scheduled": [name] if changed else [], "requires_restart": changed},
        message=(
            "Restart required to apply."
            if changed
            else "Module is already at the declared version."
        ),
    )


@router.post("/-/restart", status_code=status.HTTP_202_ACCEPTED)
async def restart_backend(
    background_tasks: BackgroundTasks,
    _: Annotated[None, Depends(require_permission("admin.clinic.write"))],
) -> ApiResponse[dict[str, Any]]:
    """Send SIGTERM to the backend process so Docker respawns it.

    The endpoint returns immediately; the actual shutdown runs in a
    background task with a small delay so the HTTP response flushes
    first. The container must have ``restart: unless-stopped`` set for
    the respawn to happen (see ``docker-compose.yml``).
    """
    background_tasks.add_task(_graceful_exit)
    return ApiResponse(
        data={"pid": os.getpid()},
        message="Restart scheduled.",
    )


async def _graceful_exit() -> None:
    await asyncio.sleep(0.5)
    logger.info("Sending SIGTERM to self (pid=%s) for module restart", os.getpid())
    os.kill(os.getpid(), signal.SIGTERM)
