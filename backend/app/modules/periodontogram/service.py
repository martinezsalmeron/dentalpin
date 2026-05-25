"""Periodontogram service layer.

PR-1 ships the class shell; concrete query methods land in PR-2.
The service stays thin and side-effect free aside from event publication
on close (PR-3). All public methods filter by ``clinic_id`` — multi-tenancy
guarantee per ``CLAUDE.md``.
"""

from __future__ import annotations


class PeriodontogramService:
    """Static service for periodontogram snapshots, teeth and sites.

    Endpoints are not wired yet — the router exposes an empty surface in
    PR-1 so the module can install without runtime errors. Concrete
    ``get_or_create_draft`` / ``update_*`` / ``close_snapshot`` methods
    arrive in PR-2.
    """
