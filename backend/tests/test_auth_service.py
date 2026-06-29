"""Tests for app.services.auth_service module."""
import uuid
from datetime import timedelta

import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_user_by_id,
    hash_password,
    register_user,
    verify_password,
)

settings = get_settings()


class TestPasswordHashing:
    def test_hash_password_returns_hash(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("secret123")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("test")
        h2 = hash_password("test")
        assert h1 != h2  # bcrypt uses random salts


class TestAccessToken:
    def test_create_and_decode_token(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        payload = decode_access_token(token)
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_token_with_custom_expiry(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id, expires_delta=timedelta(hours=2))
        payload = decode_access_token(token)
        assert payload["sub"] == user_id

    def test_expired_token_raises(self):
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_invalid_token_raises(self):
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token("not.a.valid.token")


class TestRegisterUser:
    @pytest.mark.asyncio
    async def test_register_new_user(self, db_session: AsyncSession):
        user = await register_user(db_session, "new@example.com", "password123", "New User")
        await db_session.commit()
        assert user.email == "new@example.com"
        assert user.name == "New User"
        assert user.hashed_password is not None
        assert user.hashed_password != "password123"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self, db_session: AsyncSession):
        await register_user(db_session, "dup@example.com", "pass1", "User1")
        await db_session.commit()
        with pytest.raises(ValueError, match="Email already registered"):
            await register_user(db_session, "dup@example.com", "pass2", "User2")

    @pytest.mark.asyncio
    async def test_register_creates_profile(self, db_session: AsyncSession):
        from app.models.user import UserProfile

        user = await register_user(db_session, "withprofile@example.com", "pass", "PUser")
        await db_session.commit()
        result = await db_session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        assert profile is not None
        assert profile.user_id == user.id


class TestAuthenticateUser:
    @pytest.mark.asyncio
    async def test_authenticate_success(self, db_session: AsyncSession):
        await register_user(db_session, "auth@example.com", "correctpass")
        await db_session.commit()
        user = await authenticate_user(db_session, "auth@example.com", "correctpass")
        assert user is not None
        assert user.email == "auth@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, db_session: AsyncSession):
        await register_user(db_session, "auth2@example.com", "correctpass")
        await db_session.commit()
        user = await authenticate_user(db_session, "auth2@example.com", "wrongpass")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_email(self, db_session: AsyncSession):
        user = await authenticate_user(db_session, "noexist@example.com", "password")
        assert user is None


class TestGetUserById:
    @pytest.mark.asyncio
    async def test_get_existing_user(self, db_session: AsyncSession):
        user = await register_user(db_session, "getme@example.com", "pass")
        await db_session.commit()
        found = await get_user_by_id(db_session, user.id)
        assert found is not None
        assert found.email == "getme@example.com"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, db_session: AsyncSession):
        found = await get_user_by_id(db_session, str(uuid.uuid4()))
        assert found is None
