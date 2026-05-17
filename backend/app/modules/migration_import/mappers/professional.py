"""Map ``professional`` → :class:`auth.User` + :class:`ClinicMembership`.

We create a non-loginable User shell (random unguessable password hash)
so the rest of the system can reference the professional via FK
(``appointments.professional_id``, etc.). An admin invites the
professional through the normal Users page after the import lands,
which sends a password-reset email and activates the account.

Email collisions across clinics resolve to the existing User —
DentalPin's User table is global, ClinicMembership is per-clinic.
"""

from __future__ import annotations

import secrets
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from app.core.auth.models import ClinicMembership, User

from .base import MapperContext

# Map DPMF's `role` string into DentalPin's membership role values.
# Anything unrecognised falls back to "assistant" so the user can do
# something useful while the admin re-roles.
_ROLE_MAP: dict[str, str] = {
    "dentist": "dentist",
    "hygienist": "hygienist",
    "auxiliary": "assistant",
    "assistant": "assistant",
    "receptionist": "receptionist",
    "admin": "admin",
}


class ProfessionalMapper:
    async def apply(
        self,
        ctx: MapperContext,
        *,
        entity_type: str,
        payload: dict[str, Any],
        raw: dict[str, Any],
        canonical_uuid: str,
        source_id: str,
        source_system: str,
    ) -> UUID | None:
        existing = await ctx.resolver.get("professional", canonical_uuid)
        if existing is not None:
            return existing

        email = (payload.get("email") or "").strip().lower() or None
        first_name = (payload.get("given_name") or "").strip() or "Profesional"
        last_name = (payload.get("family_name") or "").strip() or "—"

        # Fall back to a synthetic email so the User row is creatable.
        # The admin sees these in the Users page and merges/edits.
        if not email:
            slug = (
                "".join(ch.lower() for ch in f"{first_name}{last_name}" if ch.isalnum())
                or canonical_uuid[:8]
            )
            email = f"migrado+{slug}-{canonical_uuid[:8]}@dental-bridge.local"

        # Re-use an existing User if email already known.
        existing_user = await ctx.db.execute(select(User).where(User.email == email))
        user = existing_user.scalar_one_or_none()
        if user is None:
            user = User(
                id=uuid4(),
                email=email,
                # Random unguessable hash — bcrypt-like length; the user
                # cannot log in until an admin sends a password reset.
                password_hash=f"!migration_disabled:{secrets.token_urlsafe(32)}",
                first_name=first_name,
                last_name=last_name,
                is_active=False,
            )
            ctx.db.add(user)
            await ctx.db.flush()

        # Ensure membership in the target clinic.
        membership_q = await ctx.db.execute(
            select(ClinicMembership).where(
                ClinicMembership.user_id == user.id,
                ClinicMembership.clinic_id == ctx.clinic_id,
            )
        )
        membership = membership_q.scalar_one_or_none()
        if membership is None:
            role = _ROLE_MAP.get((payload.get("role") or "").lower(), "assistant")
            membership = ClinicMembership(
                id=uuid4(),
                clinic_id=ctx.clinic_id,
                user_id=user.id,
                role=role,
            )
            ctx.db.add(membership)
            await ctx.db.flush()

        await ctx.resolver.set(
            entity_type="professional",
            canonical_uuid=canonical_uuid,
            source_system=source_system,
            dentalpin_table="users",
            dentalpin_id=user.id,
        )
        return user.id
