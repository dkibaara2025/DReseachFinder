from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/grantassist"

    # Weaviate
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str = ""

    # Redis / Upstash
    redis_url: str = "redis://localhost:6379"

    # LLM providers
    openrouter_api_key: str = ""
    google_ai_studio_api_key: str = ""

    # Email
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@grantassist.ai"

    # Google Drive
    google_drive_credentials: str = ""

    # Zotero
    zotero_api_key: str = ""

    # SuperTokens
    supertokens_connection_uri: str = "http://localhost:3567"
    supertokens_api_key: str = ""

    # SerpApi
    serpapi_api_key: str = ""

    # App
    app_name: str = "GrantAssist AI"
    debug: bool = False
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    # JWT (fallback auth)
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
