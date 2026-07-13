from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey
from datetime import datetime, timezone


from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.users.user_model import User
    from app.modules.jobs.job_model import JobPost


# ---------------------------------------------------------------------------------------------------------- #


class Companies(Base):
    __tablename__ = "companies"

    company_id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str] = mapped_column(nullable=False, unique=True)
    company_address: Mapped[str] = mapped_column(nullable=False)
    company_email: Mapped[str] = mapped_column(nullable=False)
    company_phone: Mapped[str] = mapped_column(nullable=False)
    company_website: Mapped[str] = mapped_column(nullable=True)
    company_description: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    manager: Mapped["User"] = relationship("User", back_populates="companies")
    job_posts: Mapped[list["JobPost"]] = relationship("JobPost", back_populates="company")
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)