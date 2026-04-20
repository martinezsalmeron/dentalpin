"""``dentalpin modules ...`` subcommands.

Etapa 1 covers read-only queries: ``list``, ``info``, ``status``,
``doctor``, and the recovery command ``orphan``. Install, uninstall
and upgrade land in Etapa 3.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plugins import ModuleOperationError, ModuleService
from app.core.plugins.loader import discover_modules
from app.core.plugins.registry import module_registry
from app.database import async_session_maker


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("modules", help="Manage installed modules")
    mod_sub = parser.add_subparsers(dest="modules_command", required=True)

    p_list = mod_sub.add_parser("list", help="List all known modules")
    _add_json_flag(p_list)
    p_list.set_defaults(func=_run(_cmd_list))

    p_info = mod_sub.add_parser("info", help="Show module details")
    p_info.add_argument("name")
    _add_json_flag(p_info)
    p_info.set_defaults(func=_run(_cmd_info))

    p_status = mod_sub.add_parser("status", help="Summary of pending operations")
    _add_json_flag(p_status)
    p_status.set_defaults(func=_run(_cmd_status))

    p_doctor = mod_sub.add_parser("doctor", help="Diagnose module system health")
    _add_json_flag(p_doctor)
    p_doctor.set_defaults(func=_run(_cmd_doctor))

    p_orphan = mod_sub.add_parser(
        "orphan",
        help="Mark a module missing from disk as uninstalled (recovery)",
    )
    p_orphan.add_argument("name")
    p_orphan.set_defaults(func=_run(_cmd_orphan))

    p_install = mod_sub.add_parser("install", help="Schedule a module install")
    p_install.add_argument("name")
    p_install.add_argument(
        "--force",
        action="store_true",
        help="Override installable=False checks",
    )
    p_install.set_defaults(func=_run(_cmd_install))

    p_uninstall = mod_sub.add_parser("uninstall", help="Schedule a module uninstall")
    p_uninstall.add_argument("name")
    p_uninstall.add_argument(
        "--force",
        action="store_true",
        help="Override removable=False / reverse-dep checks (cannot bypass legacy block)",
    )
    p_uninstall.set_defaults(func=_run(_cmd_uninstall))

    p_upgrade = mod_sub.add_parser("upgrade", help="Schedule a module upgrade")
    p_upgrade.add_argument("name")
    p_upgrade.set_defaults(func=_run(_cmd_upgrade))

    p_restart = mod_sub.add_parser(
        "restart",
        help="Terminate backend process so docker respawns and applies pending operations",
    )
    p_restart.set_defaults(func=_run(_cmd_restart))


# --- Runners --------------------------------------------------------------


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output raw JSON",
    )


def _run(
    coro_fn: Callable[[ModuleService, argparse.Namespace], Awaitable[int]],
) -> Callable[[argparse.Namespace], Awaitable[int]]:
    async def wrapper(args: argparse.Namespace) -> int:
        # Discovery populates the in-memory registry so CLI can see modules
        # even without a running app lifespan.
        if not module_registry.list_modules():
            for module in discover_modules():
                try:
                    module_registry.register(module)
                except ValueError:
                    # Already registered (e.g. tests).
                    pass

        async with async_session_maker() as session:
            service = ModuleService(session)
            return await coro_fn(service, args)

    return wrapper


# --- Commands -------------------------------------------------------------


async def _cmd_list(svc: ModuleService, args: argparse.Namespace) -> int:
    infos = await svc.list_modules()
    data = [info.to_dict() for info in infos]

    if args.as_json:
        _print_json(data)
        return 0

    header = f"{'NAME':<20} {'VERSION':<10} {'STATE':<14} {'CATEGORY':<10} {'DEPENDS'}"
    print(header)
    print("-" * len(header))
    for info in infos:
        deps = ",".join(info.depends) if info.depends else "-"
        print(
            f"{info.name:<20} {info.version:<10} {info.state.value:<14} "
            f"{info.category.value:<10} {deps}"
        )
    return 0


async def _cmd_info(svc: ModuleService, args: argparse.Namespace) -> int:
    info = await svc.get_info(args.name)
    if info is None:
        print(f"Module not found: {args.name}", file=sys.stderr)
        return 2

    data = info.to_dict()
    if args.as_json:
        _print_json(data)
        return 0

    for key, value in data.items():
        print(f"{key}: {value}")
    return 0


async def _cmd_status(svc: ModuleService, args: argparse.Namespace) -> int:
    report = await svc.status()
    if args.as_json:
        _print_json(report)
        return 0

    print(f"Total modules: {report['total']}")
    print("By state:")
    for state, count in sorted(report["by_state"].items()):
        print(f"  {state:<14} {count}")

    if report["pending"]:
        print(f"Pending: {', '.join(report['pending'])}")
    if report["errored"]:
        print(f"Errored: {', '.join(report['errored'])}")
    return 0


async def _cmd_doctor(svc: ModuleService, args: argparse.Namespace) -> int:
    report = await svc.doctor()
    data = report.to_dict()

    if args.as_json:
        _print_json(data)
        return 0 if report.ok else 1

    if report.ok:
        print("All checks passed.")
        return 0

    if report.orphans:
        print("Orphan modules (in DB, missing from disk):")
        for name in report.orphans:
            print(f"  - {name}")
    if report.missing_dependencies:
        print("Missing dependencies:")
        for module, missing in report.missing_dependencies:
            print(f"  - {module} requires {missing}")
    if report.manifest_errors:
        print("Manifest errors:")
        for module, err in report.manifest_errors:
            print(f"  - {module}: {err}")
    if report.errored_modules:
        print("Modules with persisted errors:")
        for module, err in report.errored_modules:
            print(f"  - {module}: {err}")
    return 1


async def _cmd_orphan(svc: ModuleService, args: argparse.Namespace) -> int:
    updated = await svc.orphan(args.name)
    if not updated:
        print(f"Module not found: {args.name}", file=sys.stderr)
        return 2
    print(f"Marked {args.name} as uninstalled.")
    return 0


async def _cmd_install(svc: ModuleService, args: argparse.Namespace) -> int:
    try:
        scheduled = await svc.install(args.name, force=args.force)
    except ModuleOperationError as exc:
        print(f"Install blocked: {exc}", file=sys.stderr)
        return 3

    if not scheduled:
        print(f"{args.name} is already installed.")
        return 0

    print("Scheduled for install on next restart:")
    for item in scheduled:
        print(f"  - {item}")
    print("\nRun `dentalpin modules restart` to apply.")
    return 0


async def _cmd_uninstall(svc: ModuleService, args: argparse.Namespace) -> int:
    try:
        await svc.uninstall(args.name, force=args.force)
    except ModuleOperationError as exc:
        print(f"Uninstall blocked: {exc}", file=sys.stderr)
        return 3

    print(f"Scheduled uninstall for {args.name}.")
    print("A data backup will be taken before Alembic downgrade.")
    print("Run `dentalpin modules restart` to apply.")
    return 0


async def _cmd_upgrade(svc: ModuleService, args: argparse.Namespace) -> int:
    try:
        changed = await svc.upgrade(args.name)
    except ModuleOperationError as exc:
        print(f"Upgrade blocked: {exc}", file=sys.stderr)
        return 3

    if not changed:
        print(f"{args.name} is already at the declared version.")
        return 0

    print(f"Scheduled upgrade for {args.name}.")
    print("Run `dentalpin modules restart` to apply.")
    return 0


async def _cmd_restart(svc: ModuleService, args: argparse.Namespace) -> int:
    import os
    import signal

    pid = os.getpid()
    # The CLI runs in a separate process from the backend; signal to
    # the backend container happens via docker restart. Here we surface
    # the recommended command instead of pretending to kill ourselves.
    print(
        "The CLI cannot restart the backend from inside its own "
        "process. Either:\n"
        "  1. Hit POST /api/v1/modules/-/restart (requires auth), or\n"
        "  2. Run `docker compose restart backend` from the host."
    )
    # For completeness if ever run inside the backend container process.
    _ = pid, signal
    return 0


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


__all__ = ["register"]

# Convenience alias so typing stays tidy when imported elsewhere.
AsyncDbSession = AsyncSession
