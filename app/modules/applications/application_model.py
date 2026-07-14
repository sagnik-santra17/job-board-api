from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum


from app.core.database import Base


if TYPE_CHECKING:
    from app.modules.users.user_model import User
    from app.modules.jobs.job_model import JobPost

# ------------------------------------------------------------------------------------------------------------ #


class ApplicationStatus(str, PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class JobApplication(Base):
    __tablename__ = "applications"

    application_id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.PENDING)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    employee: Mapped["User"] = relationship("User", back_populates="applications")
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id"), nullable=False)
    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="applications")