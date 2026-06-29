"""Background tasks using Huey with Redis backend."""
import logging

from huey import RedisHuey

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

huey = RedisHuey("grantassist", url=settings.redis_url)


@huey.periodic_task(huey.crontab(hour="3", minute="0", day_of_week="1"))
def weekly_scholar_sync():
    """Sync all users' Scholar profiles weekly (Monday 3 AM)."""
    import asyncio
    asyncio.run(_sync_all_scholars())


async def _sync_all_scholars():
    from sqlalchemy import select

    from app.database import get_session_factory
    async_session_factory = get_session_factory()
    from datetime import datetime

    from app.models.user import User, UserProfile
    from app.services.scholar_service import sync_scholar_profile

    async with async_session_factory() as db:
        result = await db.execute(
            select(User).where(User.scholar_profile_url.isnot(None))
        )
        users = result.scalars().all()
        for user in users:
            try:
                data = await sync_scholar_profile(user.scholar_profile_url)
                if data:
                    prof_result = await db.execute(
                        select(UserProfile).where(UserProfile.user_id == user.id)
                    )
                    profile = prof_result.scalar_one_or_none()
                    if profile:
                        profile.publications = data.get("publications")
                        profile.h_index = data.get("h_index")
                        profile.citation_count = data.get("citation_count")
                        profile.last_synced_at = datetime.utcnow()
                logger.info(f"Synced Scholar for user {user.id}")
            except Exception as e:
                logger.error(f"Scholar sync failed for user {user.id}: {e}")
        await db.commit()


@huey.periodic_task(huey.crontab(hour="8", minute="0"))
def daily_grant_alerts():
    """Send daily grant alert emails."""
    import asyncio
    asyncio.run(_send_grant_alerts())


async def _send_grant_alerts():
    from sqlalchemy import select

    from app.database import get_session_factory
    async_session_factory = get_session_factory()
    from app.models.alert import AlertSubscription
    from app.models.user import User
    from app.services.email_service import build_grant_alert_email, send_email
    from app.services.grant_service import search_grants

    async with async_session_factory() as db:
        result = await db.execute(
            select(AlertSubscription).where(AlertSubscription.is_active.is_(True))
        )
        subs = result.scalars().all()
        for sub in subs:
            try:
                user_result = await db.execute(
                    select(User).where(User.id == sub.user_id)
                )
                user = user_result.scalar_one_or_none()
                if not user:
                    continue

                all_grants = []
                for kw in sub.keywords:
                    grants = await search_grants(db, keyword=kw, page_size=5)
                    all_grants.extend(
                        [
                            {
                                "title": g.title,
                                "agency": g.agency,
                                "deadline": str(g.deadline) if g.deadline else "N/A",
                                "award_amount": g.award_amount or "",
                            }
                            for g in grants
                        ]
                    )

                if all_grants:
                    html = build_grant_alert_email(all_grants, sub.keywords)
                    await send_email(user.email, "New Grant Matches - GrantAssist AI", html)
                    logger.info(f"Sent alert to {user.email}")
            except Exception as e:
                logger.error(f"Alert failed for sub {sub.id}: {e}")


@huey.periodic_task(huey.crontab(hour="9", minute="0"))
def deadline_reminders():
    """Send deadline reminders at 7, 3, and 1 day before deadline."""
    import asyncio
    asyncio.run(_send_deadline_reminders())


async def _send_deadline_reminders():
    from datetime import date, timedelta

    from sqlalchemy import select

    from app.database import get_session_factory
    async_session_factory = get_session_factory()
    from app.models.grant import Grant, UserGrant
    from app.models.user import User
    from app.services.email_service import build_deadline_reminder_email, send_email

    today = date.today()
    reminder_days = [7, 3, 1]

    async with async_session_factory() as db:
        for days in reminder_days:
            target_date = today + timedelta(days=days)
            result = await db.execute(
                select(UserGrant, Grant, User)
                .join(Grant, UserGrant.grant_id == Grant.id)
                .join(User, UserGrant.user_id == User.id)
                .where(Grant.deadline == target_date)
                .where(UserGrant.status.in_(["saved", "applying"]))
            )
            rows = result.all()
            for ug, grant, user in rows:
                try:
                    html = build_deadline_reminder_email(
                        {
                            "title": grant.title,
                            "agency": grant.agency,
                            "deadline": str(grant.deadline),
                            "award_amount": grant.award_amount or "",
                        },
                        days,
                    )
                    await send_email(
                        user.email,
                        f"Grant Deadline in {days} Day(s) - {grant.title}",
                        html,
                    )
                    logger.info(f"Sent {days}-day reminder to {user.email} for {grant.title}")
                except Exception as e:
                    logger.error(f"Reminder failed: {e}")
