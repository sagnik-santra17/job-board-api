from ast import mod
from typing import TYPE_CHECKING, Annotated
from fastapi import APIRouter, Depends, HTTPException, status


from app.api.dependencies import get_cache, get_current_user, set_cache
from app.modules.jobs.job_schema import CreateJob, JobResponse, JobUpdate
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

    # Creating a unique key for this specific job in Redis
    cache_key = f"job:{job_id}"

    # 1. Check cache
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    # 2. Fetch from DB
    job = await service.find_job(
        job_id=job_id,
        company_id=company_id,
        manager_id=active_user.user_id
    )

    # 3. Cache the result (convert to dict)
    job_dict = JobResponse.model_validate(job).model_dump(mode="json")
    await set_cache(cache_key, job_dict, expire_seconds=60)

    # 4. Return the job 
    return job_dict


# -------- Find All Jobs Router -------- #
@router.get("/", status_code=status.HTTP_200_OK)
async def find_all_jobs(
    service: job_service_dependency,
    active_user: current_user,
    company_id: int,
    skip: int = 0,
    limit: int = 10
):

    # Creating a completely unique cache key for the rooms
    cache_key = f"jobs:all:{company_id}:skip:{skip}:limit:{limit}"

    # 1. Check cache
    cached_data = await get_cache(cache_key)
    if cached_data:
        return cached_data

    # 2. Fetch from DB
    jobs = await service.find_all_jobs(
        company_id=company_id, 
        manager_id=active_user.user_id,
        skip=skip,
        limit=limit
    )

    # 3. Cache the result (convert to dict)
    jobs_dict = [JobResponse.model_validate(job).model_dump(mode="json") for job in jobs]
    await set_cache(cache_key, jobs_dict, expire_seconds=60)

    return jobs_dict

