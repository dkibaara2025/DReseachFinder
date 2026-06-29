from datetime import date, datetime

from pydantic import BaseModel


class GrantResponse(BaseModel):
    id: str
    title: str
    description: str | None
    agency: str | None
    award_amount: str | None
    deadline: date | None
    eligibility: str | None
    category: str | None
    source: str | None
    url: str | None
    fetched_at: datetime

    model_config = {"from_attributes": True}


class GrantSearchParams(BaseModel):
    keyword: str | None = None
    semantic_query: str | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    deadline_before: date | None = None
    deadline_after: date | None = None
    eligibility: str | None = None
    category: str | None = None
    source: str | None = None
    page: int = 1
    page_size: int = 20


class UserGrantCreate(BaseModel):
    grant_id: str
    status: str = "saved"
    notes: str | None = None


class UserGrantUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class UserGrantResponse(BaseModel):
    id: str
    user_id: str
    grant_id: str
    status: str
    notes: str | None
    saved_at: datetime
    grant: GrantResponse | None = None

    model_config = {"from_attributes": True}
