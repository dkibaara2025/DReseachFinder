import logging
import re

import httpx

logger = logging.getLogger(__name__)

CROSSREF_API = "https://api.crossref.org/works"


async def resolve_identifier(identifier: str) -> dict | None:
    """Resolve a DOI, PMID, or arXiv ID into full metadata."""
    identifier = identifier.strip()

    if _is_doi(identifier):
        return await _resolve_doi(identifier)
    elif _is_pmid(identifier):
        return await _resolve_pmid(identifier)
    elif _is_arxiv(identifier):
        return await _resolve_arxiv(identifier)
    return None


def _is_doi(s: str) -> bool:
    return bool(re.match(r"^10\.\d{4,}/", s))


def _is_pmid(s: str) -> bool:
    return bool(re.match(r"^\d{6,10}$", s)) or s.lower().startswith("pmid:")


def _is_arxiv(s: str) -> bool:
    return bool(re.match(r"^\d{4}\.\d{4,5}", s)) or s.lower().startswith("arxiv:")


async def _resolve_doi(doi: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{CROSSREF_API}/{doi}")
            resp.raise_for_status()
            data = resp.json().get("message", {})
            return _crossref_to_metadata(data)
    except Exception as e:
        logger.error(f"DOI resolution error: {e}")
        return None


async def _resolve_pmid(pmid: str) -> dict | None:
    pmid_num = pmid.replace("pmid:", "").replace("PMID:", "").strip()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pubmed/",
                params={"format": "csl", "id": pmid_num},
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "title": data.get("title", ""),
                "authors": [
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in data.get("author", [])
                ],
                "year": data.get("issued", {}).get("date-parts", [[None]])[0][0],
                "doi": data.get("DOI"),
                "pmid": pmid_num,
                "journal": data.get("container-title", ""),
                "volume": data.get("volume", ""),
                "pages": data.get("page", ""),
            }
    except Exception as e:
        logger.error(f"PMID resolution error: {e}")
        return None


async def _resolve_arxiv(arxiv_id: str) -> dict | None:
    arxiv_id = arxiv_id.replace("arxiv:", "").replace("arXiv:", "").strip()
    try:
        import xml.etree.ElementTree as ET

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "http://export.arxiv.org/api/query",
                params={"id_list": arxiv_id},
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is None:
                return None
            title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
            authors = [
                a.findtext("atom:name", "", ns)
                for a in entry.findall("atom:author", ns)
            ]
            published = entry.findtext("atom:published", "", ns)
            year = int(published[:4]) if published and len(published) >= 4 else None
            return {
                "title": title,
                "authors": authors,
                "year": year,
                "arxiv_id": arxiv_id,
                "abstract": entry.findtext("atom:summary", "", ns).strip(),
            }
    except Exception as e:
        logger.error(f"arXiv resolution error: {e}")
        return None


def _crossref_to_metadata(data: dict) -> dict:
    authors = []
    for a in data.get("author", []):
        name_parts = [a.get("given", ""), a.get("family", "")]
        authors.append(" ".join(p for p in name_parts if p))
    title_list = data.get("title", [])
    title = title_list[0] if title_list else ""
    year = None
    date_parts = data.get("published-print", data.get("published-online", {}))
    if date_parts and date_parts.get("date-parts"):
        parts = date_parts["date-parts"][0]
        if parts:
            year = parts[0]
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": data.get("DOI"),
        "journal": data.get("container-title", [""])[0] if data.get("container-title") else "",
        "volume": data.get("volume", ""),
        "pages": data.get("page", ""),
        "url": data.get("URL", ""),
    }


def format_citation(metadata: dict, style: str = "apa") -> str:
    """Format metadata into a citation string."""
    if not metadata:
        return ""

    authors = metadata.get("authors", [])
    title = metadata.get("title", "")
    year = metadata.get("year", "")
    journal = metadata.get("journal", "")
    volume = metadata.get("volume", "")
    pages = metadata.get("pages", "")
    doi = metadata.get("doi", "")

    if style == "apa":
        author_str = _format_authors_apa(authors)
        parts = [f"{author_str} ({year}).", f"{title}."]
        if journal:
            journal_part = f"*{journal}*"
            if volume:
                journal_part += f", *{volume}*"
            if pages:
                journal_part += f", {pages}"
            parts.append(f"{journal_part}.")
        if doi:
            parts.append(f"https://doi.org/{doi}")
        return " ".join(parts)

    elif style == "mla":
        author_str = _format_authors_mla(authors)
        parts = [f'{author_str} "{title}."']
        if journal:
            parts.append(f"*{journal}*,")
            if volume:
                parts.append(f"vol. {volume},")
            if year:
                parts.append(f"{year},")
            if pages:
                parts.append(f"pp. {pages}.")
        return " ".join(parts)

    elif style == "chicago":
        author_str = _format_authors_chicago(authors)
        parts = [f'{author_str} "{title}."']
        if journal:
            parts.append(f"*{journal}*")
            if volume:
                parts.append(f"{volume}")
            if year:
                parts.append(f"({year})")
            if pages:
                parts.append(f": {pages}.")
        return " ".join(parts)

    elif style == "bibtex":
        first_author_last = authors[0].split()[-1] if authors else "unknown"
        key = f"{first_author_last.lower()}{year}"
        lines = [f"@article{{{key},"]
        lines.append(f'  title = {{{title}}},')
        lines.append(f'  author = {{{" and ".join(authors)}}},')
        if journal:
            lines.append(f'  journal = {{{journal}}},')
        if year:
            lines.append(f"  year = {{{year}}},")
        if volume:
            lines.append(f"  volume = {{{volume}}},")
        if pages:
            lines.append(f"  pages = {{{pages}}},")
        if doi:
            lines.append(f"  doi = {{{doi}}},")
        lines.append("}")
        return "\n".join(lines)

    return f"{', '.join(authors)}. {title}. {year}."


def _format_authors_apa(authors: list[str]) -> str:
    if not authors:
        return ""
    if len(authors) == 1:
        return _last_first(authors[0])
    elif len(authors) == 2:
        return f"{_last_first(authors[0])}, & {_last_first(authors[1])}"
    else:
        parts = [_last_first(a) for a in authors[:19]]
        if len(authors) > 20:
            parts.append("...")
        parts.append(f"& {_last_first(authors[-1])}")
        return ", ".join(parts)


def _format_authors_mla(authors: list[str]) -> str:
    if not authors:
        return ""
    if len(authors) == 1:
        return _last_first(authors[0]) + "."
    elif len(authors) == 2:
        return f"{_last_first(authors[0])}, and {authors[1]}."
    else:
        return f"{_last_first(authors[0])}, et al."


def _format_authors_chicago(authors: list[str]) -> str:
    if not authors:
        return ""
    if len(authors) <= 3:
        formatted = [_last_first(authors[0])]
        formatted.extend(authors[1:])
        return ", and ".join(formatted) + "."
    return f"{_last_first(authors[0])}, et al."


def _last_first(name: str) -> str:
    parts = name.strip().split()
    if len(parts) < 2:
        return name
    return f"{parts[-1]}, {' '.join(parts[:-1])}"
