"""Pydantic schemas for authentication."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


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


# --- Clinic metadata admin (moved from clinical module in B.5) ---------


class ClinicAddressUpdate(BaseModel):
    """Schema for address fields on a clinic."""

    street: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)


class ClinicMetadataUpdate(BaseModel):
    """Schema for updating clinic info (admin only)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    tax_id: str | None = Field(default=None, max_length=20)
    legal_name: str | None = Field(default=None, max_length=200)
    address: ClinicAddressUpdate | None = None
    phone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"Invalid timezone '{value}'. Must be an IANA id "
                "(e.g. 'Europe/Madrid', 'America/New_York')."
            ) from exc
        return value


class _ClinicCabinetBrief(BaseModel):
    """Minimal cabinet projection for the clinic metadata endpoint.

    Agenda owns the full cabinet schema; this is a core-layer view so
    core doesn't need to import from modules.
    """

    id: UUID
    name: str
    color: str
    display_order: int = 0
    is_active: bool = True

    class Config:
        from_attributes = True


class ClinicMetadataResponse(BaseModel):
    """Schema for clinic metadata detail response."""

    id: UUID
    name: str
    tax_id: str
    legal_name: str | None = None
    address: dict | None
    phone: str | None
    email: str | None
    timezone: str
    settings: dict
    cabinets: list[_ClinicCabinetBrief]

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


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    role: str | None = Field(
        default=None, description="Role: admin, dentist, hygienist, assistant, receptionist"
    )
    is_active: bool | None = None


class ProfessionalResponse(BaseModel):
    """Schema for professional response (dentists and hygienists)."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str

    class Config:
        from_attributes = True
