import uuid
from datetime import datetime

from sqlalchemy import JSON, TIMESTAMP, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    institution: Mapped[str | None] = mapped_column(String, nullable=True)
    scholar_profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    saved_grants: Mapped[list["UserGrant"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    alert_subscriptions: Mapped[list["AlertSubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    research_interests: Mapped[list | None] = mapped_column(JSON, nullable=True)
    publications: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    orcid: Mapped[str | None] = mapped_column(String, nullable=True)
    cv_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    h_index: Mapped[int | None] = mapped_column(nullable=True)
    citation_count: Mapped[int | None] = mapped_column(nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    user: Mapped["User"] = relationship(back_populates="profile")
