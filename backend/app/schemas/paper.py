from pydantic import BaseModel


class PaperResult(BaseModel):
    title: str
    authors: list[str] = []
    year: int | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    abstract: str | None = None
    citation_count: int = 0
    source: str = ""
    url: str | None = None


class PaperSearchParams(BaseModel):
    keyword: str
    page: int = 1
    page_size: int = 20


class ReferenceRequest(BaseModel):
    identifiers: list[str]
    format: str = "apa"  # apa, mla, chicago, bibtex


class ReferenceResponse(BaseModel):
    identifier: str
    formatted_citation: str
    metadata: dict | None = None


class AlertCreate(BaseModel):
    keywords: list[str]


class AlertResponse(BaseModel):
    id: str
    keywords: list[str]
    is_active: bool

    model_config = {"from_attributes": True}
