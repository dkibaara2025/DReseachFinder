"""Tests for auth API endpoints."""
import uuid

import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        email = f"new_{uuid.uuid4().hex[:8]}@example.com"
        resp = await client.post(
            "/auth/register",
            json={"email": email, "password": "password123", "name": "New User"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == email
        assert data["user"]["name"] == "New User"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
        resp1 = await client.post(
            "/auth/register",
            json={"email": email, "password": "pass1"},
        )
        assert resp1.status_code == 201
        resp2 = await client.post(
            "/auth/register",
            json={"email": email, "password": "pass2"},
        )
        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        email = f"login_{uuid.uuid4().hex[:8]}@example.com"
        await client.post(
            "/auth/register",
            json={"email": email, "password": "mypass"},
        )
        resp = await client.post(
            "/auth/login",
            json={"email": email, "password": "mypass"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
        await client.post(
            "/auth/register",
            json={"email": email, "password": "correct"},
        )
        resp = await client.post(
            "/auth/login",
            json={"email": email, "password": "incorrect"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/auth/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient):
        resp = await client.post("/auth/logout")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "not-email", "password": "pass"},
        )
        assert resp.status_code == 422


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "GrantAssist AI"
        assert "version" in data
