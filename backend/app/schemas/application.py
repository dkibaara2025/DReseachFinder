from datetime import datetime

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    grant_id: str
    title: str | None = None


class ApplicationUpdate(BaseModel):
    title: str | None = None
    content: dict | None = None
    references_data: dict | None = None
    status: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    grant_id: str
    title: str | None
    content: dict | None
    references_data: dict | None
    status: str
    created_at: datetime
    updated_at: datetime
    pdf_url: str | None

    model_config = {"from_attributes": True}


class GenerateSectionRequest(BaseModel):
    section: str


class GenerateSectionResponse(BaseModel):
    section: str
    content: str
