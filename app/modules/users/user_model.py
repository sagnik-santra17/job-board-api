from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum

from app.core.database import Base

if TYPE_CHECKING:
   from app.modules.companies.company_model import Companies
   from app.modules.applications.application_model import JobApplication


# --------------------------------------------------------------------------------------------------------------- #


class UserType(str, PyEnum):
    EMPLOYEE = "employee"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(Enum(UserType), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    companies: Mapped[list["Companies"]] = relationship(
        "Companies", back_populates="manager"
    )
    applications: Mapped[list["JobApplication"]] = relationship(
        "JobApplication", back_populates="employee"
    )