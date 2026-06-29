"""Tests for app.services.reference_service module."""

from app.services.reference_service import (
    _crossref_to_metadata,
    _format_authors_apa,
    _format_authors_chicago,
    _format_authors_mla,
    _is_arxiv,
    _is_doi,
    _is_pmid,
    _last_first,
    format_citation,
)


class TestIdentifierDetection:
    def test_is_doi_valid(self):
        assert _is_doi("10.1038/nature12373") is True
        assert _is_doi("10.1000/xyz123") is True

    def test_is_doi_invalid(self):
        assert _is_doi("not-a-doi") is False
        assert _is_doi("1234567") is False
        assert _is_doi("2401.12345") is False

    def test_is_pmid_valid(self):
        assert _is_pmid("12345678") is True
        assert _is_pmid("PMID:12345678") is True
        assert _is_pmid("pmid:98765432") is True

    def test_is_pmid_invalid(self):
        assert _is_pmid("123") is False
        assert _is_pmid("10.1038/nature") is False

    def test_is_arxiv_valid(self):
        assert _is_arxiv("2401.12345") is True
        assert _is_arxiv("arXiv:2401.12345") is True
        assert _is_arxiv("arxiv:1906.01234") is True

    def test_is_arxiv_invalid(self):
        assert _is_arxiv("not-arxiv") is False
        assert _is_arxiv("10.1038/nature") is False


class TestLastFirst:
    def test_standard_name(self):
        assert _last_first("John Smith") == "Smith, John"

    def test_three_part_name(self):
        assert _last_first("John Michael Smith") == "Smith, John Michael"

    def test_single_name(self):
        assert _last_first("Madonna") == "Madonna"

    def test_empty_string(self):
        assert _last_first("") == ""


class TestCrossrefToMetadata:
    def test_full_metadata(self):
        data = {
            "title": ["A Great Paper"],
            "author": [
                {"given": "Jane", "family": "Doe"},
                {"given": "John", "family": "Smith"},
            ],
            "DOI": "10.1234/test",
            "published-print": {"date-parts": [[2023]]},
            "container-title": ["Nature"],
            "volume": "100",
            "page": "1-10",
            "URL": "https://doi.org/10.1234/test",
        }
        meta = _crossref_to_metadata(data)
        assert meta["title"] == "A Great Paper"
        assert len(meta["authors"]) == 2
        assert meta["authors"][0] == "Jane Doe"
        assert meta["year"] == 2023
        assert meta["doi"] == "10.1234/test"
        assert meta["journal"] == "Nature"

    def test_missing_fields(self):
        data = {"title": [], "author": []}
        meta = _crossref_to_metadata(data)
        assert meta["title"] == ""
        assert meta["authors"] == []
        assert meta["year"] is None


class TestFormatCitation:
    SAMPLE_METADATA = {
        "title": "Machine Learning in Healthcare",
        "authors": ["Jane Doe", "John Smith"],
        "year": 2023,
        "journal": "Nature Medicine",
        "volume": "29",
        "pages": "100-110",
        "doi": "10.1234/test",
    }

    def test_apa_format(self):
        result = format_citation(self.SAMPLE_METADATA, "apa")
        assert "Doe, Jane" in result
        assert "(2023)" in result
        assert "Machine Learning in Healthcare" in result
        assert "https://doi.org/10.1234/test" in result

    def test_mla_format(self):
        result = format_citation(self.SAMPLE_METADATA, "mla")
        assert "Doe, Jane" in result
        assert '"Machine Learning in Healthcare."' in result
        assert "*Nature Medicine*" in result

    def test_chicago_format(self):
        result = format_citation(self.SAMPLE_METADATA, "chicago")
        assert "Doe, Jane" in result
        assert '"Machine Learning in Healthcare."' in result
        assert "(2023)" in result

    def test_bibtex_format(self):
        result = format_citation(self.SAMPLE_METADATA, "bibtex")
        assert "@article{doe2023," in result
        assert "title = {Machine Learning in Healthcare}" in result
        assert "author = {Jane Doe and John Smith}" in result
        assert "journal = {Nature Medicine}" in result
        assert "year = {2023}" in result

    def test_unknown_format_fallback(self):
        result = format_citation(self.SAMPLE_METADATA, "unknown")
        assert "Jane Doe" in result
        assert "2023" in result

    def test_empty_metadata(self):
        assert format_citation({}, "apa") == ""
        assert format_citation(None, "apa") == ""


class TestFormatAuthorsAPA:
    def test_single_author(self):
        assert _format_authors_apa(["John Smith"]) == "Smith, John"

    def test_two_authors(self):
        result = _format_authors_apa(["John Smith", "Jane Doe"])
        assert "Smith, John" in result
        assert "& Doe, Jane" in result

    def test_three_plus_authors(self):
        result = _format_authors_apa(["A B", "C D", "E F"])
        assert "& F, E" in result

    def test_empty(self):
        assert _format_authors_apa([]) == ""


class TestFormatAuthorsMLA:
    def test_single_author(self):
        result = _format_authors_mla(["John Smith"])
        assert "Smith, John." in result

    def test_two_authors(self):
        result = _format_authors_mla(["John Smith", "Jane Doe"])
        assert "Smith, John" in result
        assert "and Jane Doe" in result

    def test_many_authors(self):
        result = _format_authors_mla(["A B", "C D", "E F", "G H"])
        assert "et al." in result


class TestFormatAuthorsChicago:
    def test_single_author(self):
        result = _format_authors_chicago(["John Smith"])
        assert "Smith, John." in result

    def test_three_authors(self):
        result = _format_authors_chicago(["A B", "C D", "E F"])
        assert "B, A" in result

    def test_four_plus_authors(self):
        result = _format_authors_chicago(["A B", "C D", "E F", "G H"])
        assert "et al." in result
