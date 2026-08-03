from datetime import datetime
from pydantic import BaseModel, Field


from app.modules.applications.application_model import ApplicationStatus


# ------------------------------------------------------------------------------------------------------ #


class CreateApplication(BaseModel):
    cover_letter: str = Field(..., min_length=3, max_length=1000)


class UpdateApplication(BaseModel):
    status: ApplicationStatus | None = Field(default=None)
    cover_letter: str | None = Field(default=None, min_length=3, max_length=1000)


class ApplicationResponse(BaseModel):
    application_id: int
    status: ApplicationStatus
    cover_letter: str | None = None
    applied_at: datetime
    updated_at: datetime
    employee_id: int
    job_id: int


class EmployeeApplicationResponse(BaseModel):
    application_id: int
    cover_letter: str | None = None
    applied_at: datetime
    updated_at: datetime
    job_id: int