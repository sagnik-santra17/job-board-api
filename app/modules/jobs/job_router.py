from typing import TYPE_CHECKING, Annotated
from fastapi import APIRouter, Depends, HTTPException, status


from app.api.dependencies import get_current_user
from app.modules.jobs.job_schema import CreateJob, JobUpdate
from app.api.dependencies import job_service_dependency


if TYPE_CHECKING:
    from app.modules.users.user_model import User


# ---------------------------------------------------------------------------------------------------------------- #


router = APIRouter(prefix="/companies/{company_id}/jobs", tags=["Jobs"])

# Current User Dependency
current_user = Annotated["User", Depends(get_current_user)]


# -------- Create Job Router -------- #
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(
    data: CreateJob,
    service: job_service_dependency,
    active_user: current_user,
    company_id: int
):
    
    if active_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can create jobs",
        )

    return await service.create_job(
        data=data, 
        company_id=company_id, 
        manager_id=active_user.user_id
    )


# -------- Update Job Router -------- #
@router.patch("/{job_id}", status_code=status.HTTP_200_OK)
async def update_job(
    data: JobUpdate,
    service: job_service_dependency,
    active_user: current_user,
    company_id: int,
    job_id: int
):

    return await service.update_job(
        data=data, 
        job_id=job_id, 
        company_id=company_id, 
        manager_id=active_user.user_id
    )


# -------- Delete Job Router -------- #
@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
async def delete_job(
    service: job_service_dependency,
    active_user: current_user,
    company_id: int,
    job_id: int
):

    return await service.delete_job(
        job_id=job_id, 
        company_id=company_id, 
        manager_id=active_user.user_id
    )


# -------- Find Job Router -------- #
@router.get("/{job_id}", status_code=status.HTTP_200_OK)
async def find_job(
    service: job_service_dependency,
    active_user: current_user,
    company_id: int,
    job_id: int
):

    return await service.find_job(
        job_id=job_id, 
        company_id=company_id, 
        manager_id=active_user.user_id
    )


# -------- Find All Jobs Router -------- #
@router.get("/", status_code=status.HTTP_200_OK)
async def find_all_jobs(
    service: job_service_dependency,
    active_user: current_user,
    company_id: int
):

    return await service.find_all_jobs(
        company_id=company_id, 
        manager_id=active_user.user_id
    )

