"""Pydantic schemas for authentication."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    professional_id: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


class ClinicResponse(BaseModel):
    """Schema for clinic response."""

    id: UUID
    name: str
    role: str  # User's role in this clinic

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    """Schema for /me endpoint response."""

    user: UserResponse
    clinics: list[ClinicResponse]
    permissions: list[str]


class AuthResponse(BaseModel):
    """Schema for auth response with user info (login/refresh)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    clinics: list[ClinicResponse]


class UserCreate(BaseModel):
    """Schema for admin creating a new user."""

    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str = Field(description="Role: admin, dentist, hygienist, assistant, receptionist")
    clinic_id: UUID | None = Field(
        default=None, description="Clinic ID. If not provided, uses admin's current clinic"
    )


class UserWithRoleResponse(BaseModel):
    """Schema for user with their clinic role."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role: str
    created_at: str

    class Config:
        from_attributes = True
