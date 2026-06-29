"""Tests for app.services.scholar_service module."""

from app.services.scholar_service import (
    _extract_publications,
    _extract_scholar_id,
    _extract_stat,
)


class TestExtractScholarId:
    def test_standard_url(self):
        url = "https://scholar.google.com/citations?user=abcDEF123&hl=en"
        assert _extract_scholar_id(url) == "abcDEF123"

    def test_url_with_extra_params(self):
        url = "https://scholar.google.com/citations?user=XYZ_789&hl=en&oi=ao"
        assert _extract_scholar_id(url) == "XYZ_789"

    def test_minimal_url(self):
        url = "https://scholar.google.com/citations?user=test123"
        assert _extract_scholar_id(url) == "test123"

    def test_no_user_param(self):
        url = "https://scholar.google.com/citations?hl=en"
        assert _extract_scholar_id(url) is None

    def test_empty_string(self):
        assert _extract_scholar_id("") is None

    def test_url_with_hyphen(self):
        url = "https://scholar.google.com/citations?user=abc-DEF_123"
        assert _extract_scholar_id(url) == "abc-DEF_123"


class TestExtractStat:
    def test_extract_h_index(self):
        html = '<td>h-index</td><td class="gsc_rsb_std">25</td>'
        assert _extract_stat(html, "h-index") == 25

    def test_extract_citations(self):
        html = '<td>Citations</td><td class="gsc_rsb_std">1500</td>'
        assert _extract_stat(html, "Citations") == 1500

    def test_stat_not_found(self):
        html = "<td>Other</td>"
        assert _extract_stat(html, "h-index") is None

    def test_empty_html(self):
        assert _extract_stat("", "h-index") is None


class TestExtractPublications:
    def test_extract_titles(self):
        html = '''
        <a class="gsc_a_at" href="/1">Paper One</a>
        <a class="gsc_a_at" href="/2">Paper Two</a>
        '''
        pubs = _extract_publications(html)
        assert len(pubs) == 2
        assert pubs[0]["title"] == "Paper One"
        assert pubs[1]["title"] == "Paper Two"

    def test_no_publications(self):
        html = "<div>No publications here</div>"
        pubs = _extract_publications(html)
        assert pubs == []

    def test_max_20_publications(self):
        html = "".join(
            f'<a class="gsc_a_at" href="/{i}">Paper {i}</a>' for i in range(30)
        )
        pubs = _extract_publications(html)
        assert len(pubs) == 20
