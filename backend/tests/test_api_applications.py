"""Tests for applications API endpoints."""
import uuid

import pytest
from httpx import AsyncClient


async def _register_and_get_headers(client: AsyncClient) -> dict:
    email = f"app_user_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/auth/register",
        json={"email": email, "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_test_grant(client: AsyncClient, db_engine) -> str:
    """Create a grant directly in DB for testing."""
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.models.grant import Grant

    grant_id = f"test_grant_{uuid.uuid4().hex[:8]}"
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        grant = Grant(
            id=grant_id,
            title="Test Grant for App",
            description="Testing",
            agency="Test Agency",
            source="grants.gov",
            fetched_at=datetime.utcnow(),
        )
        session.add(grant)
        await session.commit()
    return grant_id


class TestApplicationEndpoints:
    @pytest.mark.asyncio
    async def test_create_application(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        resp = await client.post(
            "/applications",
            json={"grant_id": grant_id, "title": "My Application"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Application"
        assert data["status"] == "draft"
        assert data["grant_id"] == grant_id

    @pytest.mark.asyncio
    async def test_create_application_nonexistent_grant(self, client: AsyncClient):
        headers = await _register_and_get_headers(client)
        resp = await client.post(
            "/applications",
            json={"grant_id": "fake_grant"},
            headers=headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_applications(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        await client.post(
            "/applications",
            json={"grant_id": grant_id, "title": "App 1"},
            headers=headers,
        )
        resp = await client.get("/applications", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_get_application(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        create_resp = await client.post(
            "/applications",
            json={"grant_id": grant_id},
            headers=headers,
        )
        app_id = create_resp.json()["id"]
        resp = await client.get(f"/applications/{app_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == app_id

    @pytest.mark.asyncio
    async def test_update_application(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        create_resp = await client.post(
            "/applications",
            json={"grant_id": grant_id},
            headers=headers,
        )
        app_id = create_resp.json()["id"]
        resp = await client.put(
            f"/applications/{app_id}",
            json={"title": "Updated Title", "content": {"background": "Some text"}},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        assert resp.json()["content"]["background"] == "Some text"

    @pytest.mark.asyncio
    async def test_delete_application(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        create_resp = await client.post(
            "/applications",
            json={"grant_id": grant_id},
            headers=headers,
        )
        app_id = create_resp.json()["id"]
        resp = await client.delete(f"/applications/{app_id}", headers=headers)
        assert resp.status_code == 204

        get_resp = await client.get(f"/applications/{app_id}", headers=headers)
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_application(self, client: AsyncClient):
        headers = await _register_and_get_headers(client)
        resp = await client.get(
            "/applications/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_invalid_section(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        create_resp = await client.post(
            "/applications",
            json={"grant_id": grant_id},
            headers=headers,
        )
        app_id = create_resp.json()["id"]
        resp = await client.post(
            f"/applications/{app_id}/generate",
            json={"section": "invalid_section"},
            headers=headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_export_application(self, client: AsyncClient, db_engine):
        headers = await _register_and_get_headers(client)
        grant_id = await _create_test_grant(client, db_engine)
        create_resp = await client.post(
            "/applications",
            json={"grant_id": grant_id, "title": "Export Test"},
            headers=headers,
        )
        app_id = create_resp.json()["id"]
        resp = await client.get(f"/applications/{app_id}/export", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["application_id"] == app_id

    @pytest.mark.asyncio
    async def test_applications_require_auth(self, client: AsyncClient):
        resp = await client.get("/applications")
        assert resp.status_code in (401, 403)
