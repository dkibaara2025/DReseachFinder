"""Tests for app.services.grant_service module."""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grant import Grant
from app.services.grant_service import (
    _parse_date,
    cache_grants,
    search_grants,
)


class TestParseDate:
    def test_iso_format(self):
        result = _parse_date("2024-06-15")
        assert result == date(2024, 6, 15)

    def test_us_format(self):
        result = _parse_date("06/15/2024")
        assert result == date(2024, 6, 15)

    def test_iso_datetime_format(self):
        result = _parse_date("2024-06-15T10:30:00")
        assert result == date(2024, 6, 15)

    def test_dash_us_format(self):
        result = _parse_date("06-15-2024")
        assert result == date(2024, 6, 15)

    def test_none_input(self):
        assert _parse_date(None) is None

    def test_empty_string(self):
        assert _parse_date("") is None

    def test_invalid_format(self):
        assert _parse_date("not-a-date") is None

    def test_integer_as_string(self):
        assert _parse_date("12345") is None


class TestCacheGrants:
    @pytest.mark.asyncio
    async def test_cache_new_grants(self, db_session: AsyncSession):
        grants_data = [
            {
                "id": "cache_test_1",
                "title": "Cached Grant 1",
                "description": "Test",
                "agency": "Agency 1",
                "source": "grants.gov",
            },
            {
                "id": "cache_test_2",
                "title": "Cached Grant 2",
                "description": "Test 2",
                "agency": "Agency 2",
                "source": "fwf",
            },
        ]
        result = await cache_grants(db_session, grants_data)
        await db_session.commit()
        assert len(result) == 2

        # Verify persisted
        db_result = await db_session.execute(select(Grant).where(Grant.id == "cache_test_1"))
        grant = db_result.scalar_one_or_none()
        assert grant is not None
        assert grant.title == "Cached Grant 1"

    @pytest.mark.asyncio
    async def test_cache_updates_stale(self, db_session: AsyncSession):
        # Insert a stale grant
        old_grant = Grant(
            id="stale_grant",
            title="Old Title",
            source="grants.gov",
            fetched_at=datetime.utcnow() - timedelta(hours=25),
        )
        db_session.add(old_grant)
        await db_session.commit()

        # Cache with updated data
        grants_data = [{"id": "stale_grant", "title": "New Title", "source": "grants.gov"}]
        result = await cache_grants(db_session, grants_data)
        await db_session.commit()

        assert len(result) == 1
        assert result[0].title == "New Title"


class TestSearchGrants:
    @pytest.mark.asyncio
    async def test_search_by_keyword(self, db_session: AsyncSession):
        g1 = Grant(id="search_1", title="Machine Learning Grant", source="grants.gov", fetched_at=datetime.utcnow())
        g2 = Grant(id="search_2", title="Biology Grant", source="fwf", fetched_at=datetime.utcnow())
        db_session.add_all([g1, g2])
        await db_session.commit()

        results = await search_grants(db_session, keyword="Machine")
        assert len(results) >= 1
        assert any(g.id == "search_1" for g in results)

    @pytest.mark.asyncio
    async def test_search_by_source(self, db_session: AsyncSession):
        g1 = Grant(id="src_1", title="Grant A", source="grants.gov", fetched_at=datetime.utcnow())
        g2 = Grant(id="src_2", title="Grant B", source="fwf", fetched_at=datetime.utcnow())
        db_session.add_all([g1, g2])
        await db_session.commit()

        results = await search_grants(db_session, source="fwf")
        assert all(g.source == "fwf" for g in results)

    @pytest.mark.asyncio
    async def test_search_with_deadline_filter(self, db_session: AsyncSession):
        g1 = Grant(id="dl_1", title="Grant 1", deadline=date(2026, 6, 1), fetched_at=datetime.utcnow())
        g2 = Grant(id="dl_2", title="Grant 2", deadline=date(2026, 12, 1), fetched_at=datetime.utcnow())
        db_session.add_all([g1, g2])
        await db_session.commit()

        results = await search_grants(db_session, deadline_before=date(2026, 8, 1))
        ids = [g.id for g in results]
        assert "dl_1" in ids

    @pytest.mark.asyncio
    async def test_search_pagination(self, db_session: AsyncSession):
        for i in range(5):
            db_session.add(Grant(id=f"page_{i}", title=f"Grant {i}", fetched_at=datetime.utcnow()))
        await db_session.commit()

        page1 = await search_grants(db_session, page=1, page_size=2)
        assert len(page1) <= 2

    @pytest.mark.asyncio
    async def test_search_no_results(self, db_session: AsyncSession):
        results = await search_grants(db_session, keyword="nonexistentxyz")
        assert results == []
