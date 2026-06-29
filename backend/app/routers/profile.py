from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserProfileResponse, UserProfileUpdate, UserResponse
from app.utils.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("", response_model=UserResponse)
async def update_profile(
    body: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.institution is not None:
        user.institution = body.institution
    if body.scholar_profile_url is not None:
        user.scholar_profile_url = body.scholar_profile_url

    # Update extended profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    if body.research_interests is not None:
        profile.research_interests = body.research_interests
    if body.orcid is not None:
        profile.orcid = body.orcid
    if body.cv_text is not None:
        profile.cv_text = body.cv_text

    await db.flush()
    return UserResponse.model_validate(user)


@router.get("/extended", response_model=UserProfileResponse)
async def get_extended_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return UserProfileResponse.model_validate(profile)


@router.post("/sync-scholar")
async def trigger_scholar_sync(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.scholar_profile_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Scholar profile URL set",
        )

    from datetime import datetime

    from app.services.scholar_service import sync_scholar_profile

    data = await sync_scholar_profile(user.scholar_profile_url)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to sync Scholar profile",
        )

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    profile.publications = data.get("publications")
    profile.h_index = data.get("h_index")
    profile.citation_count = data.get("citation_count")
    profile.last_synced_at = datetime.utcnow()
    await db.flush()

    return {"message": "Scholar profile synced", "data": data}
