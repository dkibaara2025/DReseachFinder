import uuid
from datetime import date, datetime

from sqlalchemy import TIMESTAMP, CheckConstraint, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Grant(Base):
    __tablename__ = "grants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agency: Mapped[str | None] = mapped_column(String, nullable=True)
    award_amount: Mapped[str | None] = mapped_column(String, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )

    user_grants: Mapped[list["UserGrant"]] = relationship(
        back_populates="grant", cascade="all, delete-orphan"
    )


class UserGrant(Base):
    __tablename__ = "user_grants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE")
    )
    grant_id: Mapped[str] = mapped_column(
        String, ForeignKey("grants.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String, default="saved")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    saved_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('saved','applying','submitted','awarded','rejected')",
            name="ck_user_grants_status",
        ),
    )

    user: Mapped["User"] = relationship(back_populates="saved_grants")
    grant: Mapped["Grant"] = relationship(back_populates="user_grants")
