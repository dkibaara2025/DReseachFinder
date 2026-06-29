import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application
from app.models.grant import Grant
from app.models.user import User, UserProfile
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    GenerateSectionRequest,
    GenerateSectionResponse,
)
from app.services.llm_service import generate_section
from app.services.paper_service import search_all_sources
from app.utils.deps import get_current_user

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    body: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify grant exists
    result = await db.execute(select(Grant).where(Grant.id == body.grant_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    app = Application(
        id=str(uuid.uuid4()),
        user_id=user.id,
        grant_id=body.grant_id,
        title=body.title,
        content={},
        references_data={},
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(app)
    await db.flush()
    return ApplicationResponse.model_validate(app)


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user.id)
        .order_by(Application.updated_at.desc())
    )
    apps = result.scalars().all()
    return [ApplicationResponse.model_validate(a) for a in apps]


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return ApplicationResponse.model_validate(app)


@router.put("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: str,
    body: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if body.title is not None:
        app.title = body.title
    if body.content is not None:
        app.content = body.content
    if body.references_data is not None:
        app.references_data = body.references_data
    if body.status is not None:
        app.status = body.status
    app.updated_at = datetime.utcnow()
    await db.flush()
    return ApplicationResponse.model_validate(app)


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    app_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    await db.delete(app)
    await db.flush()


@router.post("/{app_id}/generate", response_model=GenerateSectionResponse)
async def generate_application_section(
    app_id: str,
    body: GenerateSectionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    valid_sections = {"background", "goals", "methodology", "outcomes", "references"}
    if body.section not in valid_sections:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid section. Must be one of: {valid_sections}",
        )

    # Get application
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # Get grant info
    grant_result = await db.execute(select(Grant).where(Grant.id == app.grant_id))
    grant = grant_result.scalar_one_or_none()
    grant_info = {
        "title": grant.title if grant else "",
        "agency": grant.agency if grant else "",
        "description": grant.description if grant else "",
        "eligibility": grant.eligibility if grant else "",
    }

    # Get user profile
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    user_profile = {
        "name": user.name or "",
        "institution": user.institution or "",
        "research_interests": profile.research_interests or [] if profile else [],
        "publication_summary": str(profile.publications)[:200] if profile and profile.publications else "",
    }

    # Fetch relevant papers
    search_terms = grant_info["title"] or "research"
    papers = await search_all_sources(search_terms, page=1, page_size=10)
    papers_dicts = [p.model_dump() for p in papers]

    # Generate via LLM
    content = await generate_section(
        section=body.section,
        grant_info=grant_info,
        user_profile=user_profile,
        relevant_papers=papers_dicts,
        existing_content=app.content,
    )

    # Save to application
    if app.content is None:
        app.content = {}
    app.content[body.section] = content
    app.updated_at = datetime.utcnow()
    await db.flush()

    return GenerateSectionResponse(section=body.section, content=content)


@router.get("/{app_id}/export")
async def export_application(
    app_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == user.id,
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    # For now, return the content as JSON (PDF generation would require external service)
    return {
        "application_id": str(app.id),
        "title": app.title,
        "content": app.content,
        "references": app.references_data,
        "status": app.status,
        "message": "PDF export requires PDF-Turtle service configuration",
    }
