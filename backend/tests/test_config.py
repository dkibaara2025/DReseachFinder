"""Tests for app.config module."""
from app.config import Settings, get_settings


class TestSettings:
    def test_default_values(self):
        s = Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            _env_file=None,
        )
        assert s.app_name == "GrantAssist AI"
        assert s.debug is False
        assert s.algorithm == "HS256"
        assert s.access_token_expire_minutes == 60
        assert s.frontend_url == "http://localhost:5173"
        assert s.backend_url == "http://localhost:8000"

    def test_custom_values(self):
        s = Settings(
            database_url="postgresql+asyncpg://user:pass@host/db",
            redis_url="redis://custom:6380",
            debug=True,
            app_name="Custom App",
            _env_file=None,
        )
        assert s.database_url == "postgresql+asyncpg://user:pass@host/db"
        assert s.redis_url == "redis://custom:6380"
        assert s.debug is True
        assert s.app_name == "Custom App"

    def test_get_settings_returns_settings(self):
        s = get_settings()
        assert isinstance(s, Settings)
        assert s.app_name == "GrantAssist AI"

    def test_empty_api_keys_by_default(self):
        s = Settings(
            database_url="sqlite+aiosqlite:///:memory:",
            _env_file=None,
        )
        assert s.openrouter_api_key == ""
        assert s.google_ai_studio_api_key == ""
        assert s.sendgrid_api_key == ""
        assert s.weaviate_api_key == ""
        assert s.zotero_api_key == ""
        assert s.serpapi_api_key == ""
