import logging
from fastapi import HTTPException, status

from app.modules.jobs.job_model import JobPost


# ---------------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


# -------- checking if the entered job id is valid/if the job exists --------- #
def validate_job_id_exists(job: JobPost | None) -> JobPost:

    if job is None:
        logger.warning("Job lookup failed: The requested job ID does not exist.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found with that job id"
        )
    return job



# -------- Getting and validating job ownership -------- #
async def get_and_validate_job_ownership(repo, job_id: int, company_id: int) -> JobPost:

    job = await repo.find_job_by_id(job_id)

    validate_job_id_exists(job) # -> raises 404 if the job does not exist or invalid job id

    if job.company_id != company_id:
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="You are not authorized to access this job."
        )
    
    return job

    