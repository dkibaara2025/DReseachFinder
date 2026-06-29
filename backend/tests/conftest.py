import uuid
from datetime import datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.models import (  # noqa: F401
    AlertSubscription,
    Application,
    Grant,
    User,
    UserGrant,
    UserProfile,
)
from app.services.auth_service import create_access_token, hash_password


@pytest_asyncio.fixture
async def db_engine(tmp_path):
    db_path = tmp_path / "test.db"
    url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    from app.main import app

    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"testuser_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        name="Test User",
        institution="Test University",
        created_at=datetime.utcnow(),
    )
    db_session.add(user)
    profile = UserProfile(id=str(uuid.uuid4()), user_id=user_id)
    db_session.add(profile)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict:
    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_grant(db_session: AsyncSession):
    grant = Grant(
        id=f"test_grant_{uuid.uuid4().hex[:8]}",
        title="Test Research Grant",
        description="A test grant for unit testing",
        agency="Test Agency",
        award_amount="50000",
        deadline=datetime(2026, 12, 31).date(),
        eligibility="All researchers",
        category="Science",
        source="grants.gov",
        url="https://example.com/grant",
        fetched_at=datetime.utcnow(),
    )
    db_session.add(grant)
    await db_session.commit()
    return grant
