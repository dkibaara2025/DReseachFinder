"""Tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.application import ApplicationCreate, ApplicationUpdate, GenerateSectionRequest
from app.schemas.grant import GrantSearchParams, UserGrantCreate
from app.schemas.paper import AlertCreate, PaperResult, PaperSearchParams, ReferenceRequest
from app.schemas.user import UserCreate, UserLogin, UserProfileUpdate


class TestUserSchemas:
    def test_user_create_valid(self):
        u = UserCreate(email="test@example.com", password="secret123")
        assert u.email == "test@example.com"

    def test_user_create_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="secret")

    def test_user_create_with_name(self):
        u = UserCreate(email="test@example.com", password="s", name="Alice")
        assert u.name == "Alice"

    def test_user_login(self):
        u = UserLogin(email="test@example.com", password="pass")
        assert u.email == "test@example.com"

    def test_user_profile_update_partial(self):
        u = UserProfileUpdate(name="New Name")
        assert u.name == "New Name"
        assert u.institution is None

    def test_user_profile_update_all_fields(self):
        u = UserProfileUpdate(
            name="Alice",
            institution="MIT",
            scholar_profile_url="https://scholar.google.com/citations?user=abc",
            research_interests=["AI", "NLP"],
            orcid="0000-0001-2345-6789",
            cv_text="Experienced researcher...",
        )
        assert len(u.research_interests) == 2


class TestGrantSchemas:
    def test_grant_search_defaults(self):
        p = GrantSearchParams()
        assert p.page == 1
        assert p.page_size == 20
        assert p.keyword is None

    def test_grant_search_custom(self):
        p = GrantSearchParams(keyword="AI", source="grants.gov", page=2)
        assert p.keyword == "AI"
        assert p.page == 2

    def test_user_grant_create(self):
        g = UserGrantCreate(grant_id="test_123")
        assert g.grant_id == "test_123"
        assert g.status == "saved"

    def test_user_grant_create_with_status(self):
        g = UserGrantCreate(grant_id="test_123", status="applying", notes="In progress")
        assert g.status == "applying"
        assert g.notes == "In progress"


class TestApplicationSchemas:
    def test_application_create(self):
        a = ApplicationCreate(grant_id="g1")
        assert a.grant_id == "g1"
        assert a.title is None

    def test_application_update_partial(self):
        a = ApplicationUpdate(title="New Title")
        assert a.title == "New Title"
        assert a.content is None

    def test_generate_section_request(self):
        r = GenerateSectionRequest(section="background")
        assert r.section == "background"


class TestPaperSchemas:
    def test_paper_result_minimal(self):
        p = PaperResult(title="Test Paper", source="openalex")
        assert p.title == "Test Paper"
        assert p.citation_count == 0
        assert p.authors == []

    def test_paper_search_params(self):
        p = PaperSearchParams(keyword="deep learning")
        assert p.keyword == "deep learning"
        assert p.page == 1

    def test_reference_request(self):
        r = ReferenceRequest(identifiers=["10.1/a", "2401.12345"])
        assert len(r.identifiers) == 2
        assert r.format == "apa"

    def test_reference_request_custom_format(self):
        r = ReferenceRequest(identifiers=["10.1/a"], format="bibtex")
        assert r.format == "bibtex"

    def test_alert_create(self):
        a = AlertCreate(keywords=["machine learning", "genomics"])
        assert len(a.keywords) == 2
