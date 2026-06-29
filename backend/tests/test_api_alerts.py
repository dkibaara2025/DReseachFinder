"""Tests for alerts API endpoints."""
import uuid

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(client: AsyncClient) -> dict:
    email = f"alert_user_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAlertEndpoints:
    @pytest.mark.asyncio
    async def test_create_alert(self, client: AsyncClient):
        headers = await _register_and_get_headers(client)
        resp = await client.post(
            "/alerts",
            json={"keywords": ["machine learning", "genomics"]},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "machine learning" in data["keywords"]
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_alerts(self, client: AsyncClient):
        headers = await _register_and_get_headers(client)
        await client.post(
            "/alerts",
            json={"keywords": ["AI"]},
            headers=headers,
        )
        resp = await client.get("/alerts", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_delete_alert(self, client: AsyncClient):
        headers = await _register_and_get_headers(client)
        create_resp = await client.post(
            "/alerts",
            json={"keywords": ["delete-me"]},
            headers=headers,
        )
        alert_id = create_resp.json()["id"]
        resp = await client.delete(f"/alerts/{alert_id}", headers=headers)
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_nonexistent_alert(self, client: AsyncClient):
        headers = await _register_and_get_headers(client)
        resp = await client.delete(
            "/alerts/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_alerts_require_auth(self, client: AsyncClient):
        resp = await client.get("/alerts")
        assert resp.status_code in (401, 403)
