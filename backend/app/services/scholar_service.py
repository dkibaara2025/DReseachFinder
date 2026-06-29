import logging
import re

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def sync_scholar_profile(scholar_url: str) -> dict | None:
    """Sync Google Scholar profile data. Uses SerpApi if available, else scraping fallback."""
    scholar_id = _extract_scholar_id(scholar_url)
    if not scholar_id:
        logger.error(f"Could not extract Scholar ID from URL: {scholar_url}")
        return None

    if settings.serpapi_api_key:
        return await _fetch_via_serpapi(scholar_id)

    return await _fetch_via_scraping(scholar_id)


def _extract_scholar_id(url: str) -> str | None:
    match = re.search(r"user=([A-Za-z0-9_-]+)", url)
    return match.group(1) if match else None


async def _fetch_via_serpapi(scholar_id: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://serpapi.com/search.json",
                params={
                    "engine": "google_scholar_author",
                    "author_id": scholar_id,
                    "api_key": settings.serpapi_api_key,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            author = data.get("author", {})
            articles = data.get("articles", [])
            cited_by = data.get("cited_by", {})
            table = cited_by.get("table", [])
            h_index = None
            citation_count = None
            for row in table:
                if row.get("citations", {}).get("all"):
                    citation_count = row["citations"]["all"]
                if row.get("h_index", {}).get("all"):
                    h_index = row["h_index"]["all"]

            publications = []
            for art in articles[:50]:
                publications.append(
                    {
                        "title": art.get("title", ""),
                        "authors": art.get("authors", ""),
                        "year": art.get("year", ""),
                        "citations": art.get("cited_by", {}).get("value", 0),
                        "link": art.get("link", ""),
                    }
                )

            return {
                "name": author.get("name", ""),
                "affiliation": author.get("affiliations", ""),
                "h_index": h_index,
                "citation_count": citation_count,
                "publications": publications,
            }
    except Exception as e:
        logger.error(f"SerpApi Scholar fetch error: {e}")
        return None


async def _fetch_via_scraping(scholar_id: str) -> dict | None:
    """Fallback: basic scraping of Google Scholar profile page."""
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        ) as client:
            resp = await client.get(
                f"https://scholar.google.com/citations?user={scholar_id}&hl=en"
            )
            resp.raise_for_status()
            html = resp.text

            # Extract basic stats
            h_index = _extract_stat(html, "h-index")
            citations = _extract_stat(html, "Citations")

            # Extract publications (basic)
            publications = _extract_publications(html)

            return {
                "h_index": h_index,
                "citation_count": citations,
                "publications": publications,
            }
    except Exception as e:
        logger.error(f"Scholar scraping error: {e}")
        return None


def _extract_stat(html: str, label: str) -> int | None:
    pattern = rf'{label}.*?<td class="gsc_rsb_std">(\d+)</td>'
    match = re.search(pattern, html, re.DOTALL)
    return int(match.group(1)) if match else None


def _extract_publications(html: str) -> list[dict]:
    pubs = []
    pattern = r'class="gsc_a_at"[^>]*>(.*?)</a>'
    titles = re.findall(pattern, html)
    for title in titles[:20]:
        pubs.append({"title": title.strip(), "authors": "", "year": "", "citations": 0})
    return pubs
