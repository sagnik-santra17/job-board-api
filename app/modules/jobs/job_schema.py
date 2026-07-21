from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------------------------------------------------- #


# Job Schema for creating a new job
class CreateJob(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=50, max_length=1000)
    location: str = Field(..., min_length=3, max_length=100)
    salary_range: str = Field(..., min_length=3, max_length=100)


# Job update schema
class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=50, max_length=1000)
    location: str | None = Field(default=None, min_length=3, max_length=100)
    salary_range: str | None = Field(default=None, min_length=3, max_length=100)


# Job schema for response
class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: int
    company_id: int
    title: str
    description: str
    location: str
    salary_range: str
    is_active: bool
    created_at: datetime


