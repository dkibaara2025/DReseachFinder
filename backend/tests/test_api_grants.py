"""Tests for grants API endpoints."""
import uuid

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(client: AsyncClient) -> dict:
    email = f"grant_user_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_test_grant(client: AsyncClient, db_engine) -> str:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.models.grant import Grant

    grant_id = f"test_grant_{uuid.uuid4().hex[:8]}"
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        grant = Grant(
            id=grant_id,
            title="Test Research Grant",
            description="A test grant",
            agency="Test Agency",
            award_amount="50000",
            source="grants.gov",
            url="https://example.com/grant",
            fetched_at=datetime.utcnow(),
        )
        session.add(grant)
        await session.commit()
    return grant_id


class TestGrantsEndpoints:
    @pytest.mark.asyncio
    async def test_get_grant_by_id(self, client: AsyncClient, db_engine):
        grant_id = await _create_test_grant(client, db_engine)
        resp = await client.get(f"/grants/{grant_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Research Grant"

    @pytest.mark.asyncio
    async def test_get_grant_not_found(self, client: AsyncClient):
        resp = await client.get("/grants/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_save_grant(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        resp = await client.post(
            "/grants/save",
            json={"grant_id": grant_id},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["grant_id"] == grant_id
        assert resp.json()["status"] == "saved"

    @pytest.mark.asyncio
    async def test_save_grant_duplicate(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        await client.post(
            "/grants/save",
            json={"grant_id": grant_id},
            headers=headers,
        )
        resp = await client.post(
            "/grants/save",
            json={"grant_id": grant_id},
            headers=headers,
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_save_nonexistent_grant(self, client: AsyncClient):
        headers = await _register_and_get_headers(client)
        resp = await client.post(
            "/grants/save",
            json={"grant_id": "does_not_exist"},
            headers=headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_saved_grants(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        await client.post(
            "/grants/save",
            json={"grant_id": grant_id},
            headers=headers,
        )
        resp = await client.get("/grants/saved/list", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_save_requires_auth(self, client: AsyncClient, db_engine):
        grant_id = await _create_test_grant(client, db_engine)
        resp = await client.post(
            "/grants/save",
            json={"grant_id": grant_id},
        )
        assert resp.status_code in (401, 403)
