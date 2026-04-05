"""Authentication router with rate limiting."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.plugins import module_registry
from app.database import get_db

from .dependencies import ClinicContext, get_clinic_context, get_current_user, require_permission
from .models import ClinicMembership, User
from .permissions import CORE_PERMISSIONS, ROLES, expand_permissions, get_role_permissions
from .schemas import (
    AuthResponse,
    ClinicResponse,
    MeResponse,
    ProfessionalResponse,
    TokenRefresh,
    TokenResponse,
    UserCreate,
    UserRegister,
    UserResponse,
    UserUpdate,
    UserWithRoleResponse,
)
from .service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_strength,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address, enabled=not settings.TESTING)


@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/hour")
async def register(
    request: Request,
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Register a new user account."""
    # Validate password strength
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
    )
    db.add(user)
    await db.flush()

    # Generate tokens
    access_token = create_access_token(user.id, token_version=user.token_version)
    refresh_token = create_refresh_token(user.id, token_version=user.token_version)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login and get access tokens."""
    # Find user by email
    result = await db.execute(
        select(User).options(selectinload(User.memberships)).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Get first clinic ID if user has any membership
    clinic_id = None
    if user.memberships:
        clinic_id = user.memberships[0].clinic_id

    # Generate tokens
    access_token = create_access_token(
        user.id,
        clinic_id=clinic_id,
        token_version=user.token_version,
    )
    refresh_token = create_refresh_token(user.id, token_version=user.token_version)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthResponse:
    """Refresh access token using refresh token."""
    try:
        payload = decode_token(data.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        token_version = payload.get("token_version", 0)

        if user_id is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Fetch user with memberships and clinics
    result = await db.execute(
        select(User).options(selectinload(User.memberships)).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Check token version for revocation
    if user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    # Fetch memberships with clinics for response
    memberships_result = await db.execute(
        select(ClinicMembership)
        .options(selectinload(ClinicMembership.clinic))
        .where(ClinicMembership.user_id == user.id)
    )
    memberships = memberships_result.scalars().all()

    clinics = [
        ClinicResponse(
            id=m.clinic.id,
            name=m.clinic.name,
            role=m.role,
        )
        for m in memberships
    ]

    # Get first clinic ID for token
    clinic_id = None
    if memberships:
        clinic_id = memberships[0].clinic_id

    # Generate new tokens
    access_token = create_access_token(
        user.id,
        clinic_id=clinic_id,
        token_version=user.token_version,
    )
    new_refresh_token = create_refresh_token(user.id, token_version=user.token_version)

    return AuthResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user),
        clinics=clinics,
    )


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    """Get current user info, clinics, and permissions."""
    # Fetch memberships with clinics
    result = await db.execute(
        select(ClinicMembership)
        .options(selectinload(ClinicMembership.clinic))
        .where(ClinicMembership.user_id == current_user.id)
    )
    memberships = result.scalars().all()

    clinics = [
        ClinicResponse(
            id=m.clinic.id,
            name=m.clinic.name,
            role=m.role,
        )
        for m in memberships
    ]

    # Compute effective permissions (use first clinic's role for MVP)
    permissions: list[str] = []
    if memberships:
        role = memberships[0].role
        role_perms = get_role_permissions(role)
        # Combine module permissions with core permissions
        all_perms = module_registry.get_all_permissions() + CORE_PERMISSIONS
        permissions = expand_permissions(role_perms, all_perms)

    return MeResponse(
        user=UserResponse.model_validate(current_user),
        clinics=clinics,
        permissions=permissions,
    )


@router.get("/users", response_model=list[UserWithRoleResponse])
async def list_users(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.users.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserWithRoleResponse]:
    """List all users in the current clinic (admin only)."""
    # Fetch all memberships for this clinic with user data
    result = await db.execute(
        select(ClinicMembership)
        .options(selectinload(ClinicMembership.user))
        .where(ClinicMembership.clinic_id == ctx.clinic_id)
    )
    memberships = result.scalars().all()

    return [
        UserWithRoleResponse(
            id=m.user.id,
            email=m.user.email,
            first_name=m.user.first_name,
            last_name=m.user.last_name,
            is_active=m.user.is_active,
            role=m.role,
            created_at=m.user.created_at.isoformat(),
        )
        for m in memberships
    ]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.users.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Create a new user (admin only)."""
    # Validate role
    if data.role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of: {', '.join(ROLES)}",
        )

    # Validate password strength
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
    )
    db.add(user)
    await db.flush()

    # Create clinic membership
    clinic_id = data.clinic_id if data.clinic_id else ctx.clinic_id
    membership = ClinicMembership(
        user_id=user.id,
        clinic_id=clinic_id,
        role=data.role,
    )
    db.add(membership)
    await db.commit()

    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserWithRoleResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.users.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserWithRoleResponse:
    """Update a user in the current clinic (admin only)."""
    # Verify user belongs to this clinic
    result = await db.execute(
        select(ClinicMembership)
        .options(selectinload(ClinicMembership.user))
        .where(ClinicMembership.user_id == user_id)
        .where(ClinicMembership.clinic_id == ctx.clinic_id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this clinic",
        )

    user = membership.user

    # Prevent admin from deactivating themselves
    if data.is_active is False and user.id == ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    # Validate role if provided
    if data.role is not None and data.role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of: {', '.join(ROLES)}",
        )

    # Check email uniqueness if changing email
    if data.email is not None and data.email != user.email:
        email_check = await db.execute(select(User).where(User.email == data.email))
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user.email = data.email

    # Update user fields
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.is_active is not None:
        user.is_active = data.is_active
        # Increment token version to invalidate existing tokens when deactivating
        if not data.is_active:
            user.token_version += 1

    # Update role in membership
    if data.role is not None:
        membership.role = data.role

    await db.commit()
    await db.refresh(user)
    await db.refresh(membership)

    return UserWithRoleResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        role=membership.role,
        created_at=user.created_at.isoformat(),
    )


@router.get("/professionals", response_model=list[ProfessionalResponse])
async def list_professionals(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("clinical.appointments.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ProfessionalResponse]:
    """List professionals (dentists and hygienists) in the current clinic."""
    # Fetch memberships with dentist/hygienist role and active users
    result = await db.execute(
        select(ClinicMembership)
        .options(selectinload(ClinicMembership.user))
        .where(
            ClinicMembership.clinic_id == ctx.clinic_id,
            ClinicMembership.role.in_(["dentist", "hygienist"]),
        )
    )
    memberships = result.scalars().all()

    return [
        ProfessionalResponse(
            id=m.user.id,
            email=m.user.email,
            first_name=m.user.first_name,
            last_name=m.user.last_name,
            role=m.role,
        )
        for m in memberships
        if m.user.is_active
    ]


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("admin.users.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Remove a user from the current clinic (admin only).

    This removes the clinic membership but does not delete the user account.
    """
    # Prevent admin from removing themselves
    if user_id == ctx.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the clinic",
        )

    # Verify user belongs to this clinic
    result = await db.execute(
        select(ClinicMembership)
        .where(ClinicMembership.user_id == user_id)
        .where(ClinicMembership.clinic_id == ctx.clinic_id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this clinic",
        )

    await db.delete(membership)
    await db.commit()
