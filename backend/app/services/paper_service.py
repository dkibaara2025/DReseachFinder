import asyncio
import logging

import httpx

from app.schemas.paper import PaperResult

logger = logging.getLogger(__name__)

OPENALEX_API = "https://api.openalex.org/works"
CROSSREF_API = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV_API = "http://export.arxiv.org/api/query"


async def search_openalex(keyword: str, page: int = 1, page_size: int = 10) -> list[PaperResult]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                OPENALEX_API,
                params={
                    "search": keyword,
                    "per_page": page_size,
                    "page": page,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for work in data.get("results", []):
                authors = []
                for authorship in work.get("authorships", []):
                    author = authorship.get("author", {})
                    if author.get("display_name"):
                        authors.append(author["display_name"])
                results.append(
                    PaperResult(
                        title=work.get("title", ""),
                        authors=authors,
                        year=work.get("publication_year"),
                        doi=work.get("doi", "").replace("https://doi.org/", "") if work.get("doi") else None,
                        abstract=work.get("abstract_inverted_index") and _reconstruct_abstract(
                            work["abstract_inverted_index"]
                        ),
                        citation_count=work.get("cited_by_count", 0),
                        source="openalex",
                        url=work.get("doi") or work.get("id"),
                    )
                )
            return results
    except Exception as e:
        logger.error(f"OpenAlex error: {e}")
        return []


async def search_crossref(keyword: str, page: int = 1, page_size: int = 10) -> list[PaperResult]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                CROSSREF_API,
                params={
                    "query": keyword,
                    "rows": page_size,
                    "offset": (page - 1) * page_size,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("message", {}).get("items", []):
                authors = []
                for a in item.get("author", []):
                    name_parts = [a.get("given", ""), a.get("family", "")]
                    authors.append(" ".join(p for p in name_parts if p))
                title_list = item.get("title", [])
                title = title_list[0] if title_list else ""
                year = None
                date_parts = item.get("published-print", item.get("published-online", {}))
                if date_parts and date_parts.get("date-parts"):
                    parts = date_parts["date-parts"][0]
                    if parts:
                        year = parts[0]
                results.append(
                    PaperResult(
                        title=title,
                        authors=authors,
                        year=year,
                        doi=item.get("DOI"),
                        abstract=item.get("abstract", "").replace("<jats:p>", "").replace("</jats:p>", ""),
                        citation_count=item.get("is-referenced-by-count", 0),
                        source="crossref",
                        url=item.get("URL"),
                    )
                )
            return results
    except Exception as e:
        logger.error(f"Crossref error: {e}")
        return []


async def search_semantic_scholar(keyword: str, page: int = 1, page_size: int = 10) -> list[PaperResult]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                SEMANTIC_SCHOLAR_API,
                params={
                    "query": keyword,
                    "limit": page_size,
                    "offset": (page - 1) * page_size,
                    "fields": "title,authors,year,externalIds,abstract,citationCount,url",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for paper in data.get("data", []):
                ext_ids = paper.get("externalIds", {}) or {}
                results.append(
                    PaperResult(
                        title=paper.get("title", ""),
                        authors=[a.get("name", "") for a in paper.get("authors", [])],
                        year=paper.get("year"),
                        doi=ext_ids.get("DOI"),
                        arxiv_id=ext_ids.get("ArXiv"),
                        abstract=paper.get("abstract"),
                        citation_count=paper.get("citationCount", 0),
                        source="semantic_scholar",
                        url=paper.get("url"),
                    )
                )
            return results
    except Exception as e:
        logger.error(f"Semantic Scholar error: {e}")
        return []


async def search_arxiv(keyword: str, page: int = 1, page_size: int = 10) -> list[PaperResult]:
    try:
        import xml.etree.ElementTree as ET

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                ARXIV_API,
                params={
                    "search_query": f"all:{keyword}",
                    "start": (page - 1) * page_size,
                    "max_results": page_size,
                },
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            results = []
            for entry in root.findall("atom:entry", ns):
                title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
                authors = [
                    a.findtext("atom:name", "", ns)
                    for a in entry.findall("atom:author", ns)
                ]
                abstract = entry.findtext("atom:summary", "", ns).strip()
                arxiv_id_raw = entry.findtext("atom:id", "", ns)
                arxiv_id = arxiv_id_raw.split("/abs/")[-1] if "/abs/" in arxiv_id_raw else ""
                published = entry.findtext("atom:published", "", ns)
                year = int(published[:4]) if published and len(published) >= 4 else None
                results.append(
                    PaperResult(
                        title=title,
                        authors=authors,
                        year=year,
                        arxiv_id=arxiv_id,
                        abstract=abstract,
                        citation_count=0,
                        source="arxiv",
                        url=arxiv_id_raw,
                    )
                )
            return results
    except Exception as e:
        logger.error(f"arXiv error: {e}")
        return []


async def search_all_sources(keyword: str, page: int = 1, page_size: int = 10) -> list[PaperResult]:
    """Query all sources in parallel, deduplicate, sort by citations then recency."""
    tasks = [
        search_openalex(keyword, page, page_size),
        search_crossref(keyword, page, page_size),
        search_semantic_scholar(keyword, page, page_size),
        search_arxiv(keyword, page, page_size),
    ]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    papers: list[PaperResult] = []
    for result in all_results:
        if isinstance(result, list):
            papers.extend(result)

    deduped = _deduplicate(papers)
    deduped.sort(key=lambda p: (-p.citation_count, -(p.year or 0)))
    return deduped


def _deduplicate(papers: list[PaperResult]) -> list[PaperResult]:
    """Deduplicate by DOI or title similarity."""
    seen_dois: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[PaperResult] = []
    for p in papers:
        if p.doi and p.doi in seen_dois:
            continue
        norm_title = p.title.lower().strip()
        if norm_title in seen_titles:
            continue
        if p.doi:
            seen_dois.add(p.doi)
        seen_titles.add(norm_title)
        unique.append(p)
    return unique


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return ""
    word_positions: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort(key=lambda x: x[0])
    return " ".join(w for _, w in word_positions)
