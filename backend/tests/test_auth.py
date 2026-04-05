"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient) -> None:
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test that duplicate email registration fails."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "SecurePass123",
        "first_name": "First",
        "last_name": "User",
    }

    # First registration should succeed
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200

    # Second registration should fail
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 409
    assert "already registered" in response.json()["message"]


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient) -> None:
    """Test that weak passwords are rejected."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "weak",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login(client: AsyncClient) -> None:
    """Test user login."""
    # First register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "SecurePass123",
            "first_name": "Login",
            "last_name": "User",
        },
    )

    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "login@example.com", "password": "SecurePass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    """Test /me endpoint returns current user wrapped in ApiResponse."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Response is wrapped in ApiResponse: {data: {user, clinics, permissions}, message}
    assert data["data"]["user"]["email"] == "test@example.com"
    assert data["data"]["user"]["first_name"] == "Test"
    assert "message" in data  # message field is present (may be null)


@pytest.mark.asyncio
async def test_me_without_auth(client: AsyncClient) -> None:
    """Test /me endpoint requires authentication."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
