from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    institution: str | None
    scholar_profile_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    name: str | None = None
    institution: str | None = None
    scholar_profile_url: str | None = None
    research_interests: list[str] | None = None
    orcid: str | None = None
    cv_text: str | None = None


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    research_interests: list[str] | None
    publications: dict | None
    orcid: str | None
    cv_text: str | None
    h_index: int | None
    citation_count: int | None
    last_synced_at: datetime | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
