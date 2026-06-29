"""Tests for app.services.paper_service module."""

from app.schemas.paper import PaperResult
from app.services.paper_service import (
    _deduplicate,
    _reconstruct_abstract,
)


class TestDeduplicate:
    def test_dedup_by_doi(self):
        papers = [
            PaperResult(title="Paper A", doi="10.1/a", citation_count=5, source="openalex"),
            PaperResult(title="Paper B", doi="10.1/a", citation_count=3, source="crossref"),
            PaperResult(title="Paper C", doi="10.1/c", citation_count=1, source="arxiv"),
        ]
        result = _deduplicate(papers)
        assert len(result) == 2
        assert result[0].title == "Paper A"
        assert result[1].title == "Paper C"

    def test_dedup_by_title(self):
        papers = [
            PaperResult(title="Same Title", citation_count=5, source="openalex"),
            PaperResult(title="Same Title", citation_count=3, source="crossref"),
            PaperResult(title="Different Title", citation_count=1, source="arxiv"),
        ]
        result = _deduplicate(papers)
        assert len(result) == 2

    def test_dedup_case_insensitive_title(self):
        papers = [
            PaperResult(title="Machine Learning", citation_count=5, source="a"),
            PaperResult(title="machine learning", citation_count=3, source="b"),
        ]
        result = _deduplicate(papers)
        assert len(result) == 1

    def test_empty_list(self):
        assert _deduplicate([]) == []

    def test_no_duplicates(self):
        papers = [
            PaperResult(title="A", doi="10.1/a", citation_count=1, source="a"),
            PaperResult(title="B", doi="10.1/b", citation_count=2, source="b"),
        ]
        result = _deduplicate(papers)
        assert len(result) == 2


class TestReconstructAbstract:
    def test_basic_reconstruction(self):
        inverted = {"Hello": [0], "world": [1], "foo": [2]}
        result = _reconstruct_abstract(inverted)
        assert result == "Hello world foo"

    def test_word_at_multiple_positions(self):
        inverted = {"the": [0, 3], "quick": [1], "brown": [2], "fox": [4]}
        result = _reconstruct_abstract(inverted)
        assert result == "the quick brown the fox"

    def test_empty_index(self):
        assert _reconstruct_abstract({}) == ""

    def test_none_index(self):
        assert _reconstruct_abstract(None) == ""


class TestPaperResultModel:
    def test_paper_result_defaults(self):
        p = PaperResult(title="Test", source="test")
        assert p.authors == []
        assert p.year is None
        assert p.doi is None
        assert p.citation_count == 0

    def test_paper_result_full(self):
        p = PaperResult(
            title="Full Paper",
            authors=["Alice", "Bob"],
            year=2024,
            doi="10.1/test",
            arxiv_id="2401.00001",
            abstract="An abstract.",
            citation_count=42,
            source="semantic_scholar",
            url="https://example.com",
        )
        assert p.title == "Full Paper"
        assert len(p.authors) == 2
        assert p.citation_count == 42
