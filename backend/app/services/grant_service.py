import logging
from datetime import date, datetime, timedelta

import httpx
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grant import Grant

logger = logging.getLogger(__name__)

GRANTS_GOV_API = "https://api.grants.gov/v1/opportunities"
FWF_API = "https://www.fwf.ac.at/en/research-radar/api/v1/projects"
CACHE_TTL_HOURS = 24


async def fetch_grants_gov(keyword: str | None = None) -> list[dict]:
    """Fetch grants from Grants.gov public API."""
    params = {"page": 1, "perPage": 50}
    if keyword:
        params["keyword"] = keyword

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(GRANTS_GOV_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            opportunities = data.get("opportunities", data.get("data", []))
            results = []
            for opp in opportunities:
                results.append(
                    {
                        "id": f"grants_gov_{opp.get('id', opp.get('opportunityId', ''))}",
                        "title": opp.get("title", opp.get("opportunityTitle", "")),
                        "description": opp.get("description", opp.get("synopsis", "")),
                        "agency": opp.get("agency", opp.get("agencyName", "")),
                        "award_amount": opp.get("awardCeiling", opp.get("award", "")),
                        "deadline": _parse_date(
                            opp.get("closeDate", opp.get("deadline", ""))
                        ),
                        "eligibility": opp.get(
                            "eligibility", opp.get("applicantTypes", "")
                        ),
                        "category": opp.get("category", opp.get("fundingCategory", "")),
                        "source": "grants.gov",
                        "url": f"https://www.grants.gov/search-results-detail/{opp.get('id', opp.get('opportunityId', ''))}",
                    }
                )
            return results
    except Exception as e:
        logger.error(f"Grants.gov fetch error: {e}")
        return []


async def fetch_fwf_grants(keyword: str | None = None) -> list[dict]:
    """Fetch grants from FWF Open API."""
    params = {"limit": 50}
    if keyword:
        params["search"] = keyword

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(FWF_API, params=params)
            resp.raise_for_status()
            data = resp.json()
            projects = data.get("data", data.get("projects", []))
            results = []
            for proj in projects:
                results.append(
                    {
                        "id": f"fwf_{proj.get('id', proj.get('projectId', ''))}",
                        "title": proj.get("title", ""),
                        "description": proj.get("abstract", proj.get("description", "")),
                        "agency": "FWF - Austrian Science Fund",
                        "award_amount": str(proj.get("grantedAmount", "")),
                        "deadline": _parse_date(proj.get("endDate", "")),
                        "eligibility": proj.get("eligibility", ""),
                        "category": proj.get("researchArea", proj.get("discipline", "")),
                        "source": "fwf",
                        "url": proj.get("url", ""),
                    }
                )
            return results
    except Exception as e:
        logger.error(f"FWF fetch error: {e}")
        return []


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%m-%d-%Y"):
        try:
            return datetime.strptime(str(date_str), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


async def cache_grants(db: AsyncSession, grants_data: list[dict]) -> list[Grant]:
    """Upsert grants into PostgreSQL cache."""
    cached = []
    for g in grants_data:
        existing = await db.execute(select(Grant).where(Grant.id == g["id"]))
        grant = existing.scalar_one_or_none()
        if grant:
            # Update if stale (older than TTL)
            if grant.fetched_at < datetime.utcnow() - timedelta(hours=CACHE_TTL_HOURS):
                for key, val in g.items():
                    if key != "id" and val:
                        setattr(grant, key, val)
                grant.fetched_at = datetime.utcnow()
        else:
            grant = Grant(**g, fetched_at=datetime.utcnow())
            db.add(grant)
        cached.append(grant)
    await db.flush()
    return cached


async def search_grants(
    db: AsyncSession,
    keyword: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    deadline_before: date | None = None,
    deadline_after: date | None = None,
    eligibility: str | None = None,
    category: str | None = None,
    source: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> list[Grant]:
    """Search cached grants with filters."""
    query = select(Grant)
    conditions = []

    if keyword:
        conditions.append(
            or_(
                Grant.title.ilike(f"%{keyword}%"),
                Grant.description.ilike(f"%{keyword}%"),
            )
        )
    # Amount filtering is done in application code to support all DB backends
    # min_amount/max_amount are handled post-query if needed
    if deadline_before:
        conditions.append(Grant.deadline <= deadline_before)
    if deadline_after:
        conditions.append(Grant.deadline >= deadline_after)
    if eligibility:
        conditions.append(Grant.eligibility.ilike(f"%{eligibility}%"))
    if category:
        conditions.append(Grant.category.ilike(f"%{category}%"))
    if source:
        conditions.append(Grant.source == source)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all())
