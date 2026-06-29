import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.grant import Grant, UserGrant
from app.models.user import User
from app.schemas.grant import (
    GrantResponse,
    UserGrantCreate,
    UserGrantResponse,
    UserGrantUpdate,
)
from app.services.grant_service import (
    cache_grants,
    fetch_fwf_grants,
    fetch_grants_gov,
    search_grants,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/grants", tags=["Grants"])


@router.get("", response_model=list[GrantResponse])
async def list_grants(
    keyword: str | None = Query(None),
    semantic_query: str | None = Query(None),
    min_amount: float | None = Query(None),
    max_amount: float | None = Query(None),
    deadline_before: str | None = Query(None),
    deadline_after: str | None = Query(None),
    eligibility: str | None = Query(None),
    category: str | None = Query(None),
    source: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Try to fetch fresh data if keyword search
    if keyword:
        gov_grants = await fetch_grants_gov(keyword)
        fwf_grants = await fetch_fwf_grants(keyword)
        all_raw = gov_grants + fwf_grants
        if all_raw:
            await cache_grants(db, all_raw)

    from datetime import date as date_type

    db_before = None
    db_after = None
    if deadline_before:
        try:
            db_before = date_type.fromisoformat(deadline_before)
        except ValueError:
            pass
    if deadline_after:
        try:
            db_after = date_type.fromisoformat(deadline_after)
        except ValueError:
            pass

    results = await search_grants(
        db,
        keyword=keyword,
        min_amount=min_amount,
        max_amount=max_amount,
        deadline_before=db_before,
        deadline_after=db_after,
        eligibility=eligibility,
        category=category,
        source=source,
        page=page,
        page_size=page_size,
    )
    return [GrantResponse.model_validate(g) for g in results]


@router.get("/{grant_id}", response_model=GrantResponse)
async def get_grant(grant_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Grant).where(Grant.id == grant_id))
    grant = result.scalar_one_or_none()
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")
    return GrantResponse.model_validate(grant)


@router.post("/save", response_model=UserGrantResponse, status_code=status.HTTP_201_CREATED)
async def save_grant(
    body: UserGrantCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check grant exists
    result = await db.execute(select(Grant).where(Grant.id == body.grant_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    # Check not already saved
    existing = await db.execute(
        select(UserGrant).where(
            UserGrant.user_id == user.id,
            UserGrant.grant_id == body.grant_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Grant already saved")

    ug = UserGrant(
        id=str(uuid.uuid4()),
        user_id=user.id,
        grant_id=body.grant_id,
        status=body.status,
        notes=body.notes,
    )
    db.add(ug)
    await db.flush()
    return UserGrantResponse(
        id=ug.id,
        user_id=ug.user_id,
        grant_id=ug.grant_id,
        status=ug.status,
        notes=ug.notes,
        saved_at=ug.saved_at,
        grant=None,
    )


@router.get("/saved/list", response_model=list[UserGrantResponse])
async def list_saved_grants(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserGrant)
        .options(selectinload(UserGrant.grant))
        .where(UserGrant.user_id == user.id)
        .order_by(UserGrant.saved_at.desc())
    )
    user_grants = result.scalars().all()
    responses = []
    for ug in user_grants:
        resp = UserGrantResponse.model_validate(ug)
        if ug.grant:
            resp.grant = GrantResponse.model_validate(ug.grant)
        responses.append(resp)
    return responses


@router.put("/saved/{user_grant_id}", response_model=UserGrantResponse)
async def update_saved_grant(
    user_grant_id: str,
    body: UserGrantUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserGrant).where(
            UserGrant.id == user_grant_id,
            UserGrant.user_id == user.id,
        )
    )
    ug = result.scalar_one_or_none()
    if not ug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved grant not found")

    if body.status is not None:
        ug.status = body.status
    if body.notes is not None:
        ug.notes = body.notes
    await db.flush()
    return UserGrantResponse.model_validate(ug)


@router.delete("/saved/{user_grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_grant(
    user_grant_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserGrant).where(
            UserGrant.id == user_grant_id,
            UserGrant.user_id == user.id,
        )
    )
    ug = result.scalar_one_or_none()
    if not ug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved grant not found")
    await db.delete(ug)
    await db.flush()
