from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# ------------------------------------------------------------------------------------------------------------------- #


class JobPost(Base):
    __tablename__ = "jobs"

    job_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)  
    location: Mapped[str] = mapped_column(nullable=False)
    salary_range: Mapped[str] = mapped_column(nullable=True) 
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationshipal fields
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.company_id"), nullable=False)