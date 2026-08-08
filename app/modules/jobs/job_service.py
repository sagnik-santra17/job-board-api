import logging
from fastapi import HTTPException, status

from app.modules.companies.company_repository import CompanyRepository
from app.modules.jobs.job_model import JobPost
from app.modules.jobs.job_repository import JobRepository
from app.modules.jobs.job_schema import CreateJob, JobUpdate
from app.utils.company_utils import get_and_validate_company_ownership
from app.utils.job_utils import get_and_validate_job_ownership


# ------------------------------------------------------------------------------------------------------------------ #


logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, repo: JobRepository, company_repo: CompanyRepository):
        self.repo = repo
        self.company_repo = company_repo


    # Creating a new job post
    async def create_job(self, data: CreateJob, company_id: int, manager_id: int) -> JobPost:

        logger.info(f"Service: Manager {manager_id} creating job for company: {company_id}")

        await get_and_validate_company_ownership(
            self.company_repo, 
            company_id, 
            manager_id
        )

        duplicate_job_title = await self.repo.find_job_by_title(data.title, company_id)

        if duplicate_job_title:
            logger.warning(f"Service: Create failed. Job already exists with title: {data.title}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job already exists with title."
            )   


        new_job = JobPost(**data.model_dump(), company_id=company_id)

        created_job = await self.repo.create(new_job)

        logger.info(f"Service: Job {created_job.title} (ID: {created_job.job_id}) created successfully")

        return created_job


    # Updating a job post
    async def update_job(self, data: JobUpdate, job_id: int, company_id: int, manager_id: int) -> JobPost:

        logger.info(f"Service: Manager {manager_id} updating job: {job_id}")

        await get_and_validate_company_ownership(
            self.company_repo, 
            company_id, 
            manager_id
        )    

        valid_job = await get_and_validate_job_ownership(
            self.repo, 
            job_id, 
            company_id
        )
        

        # Check duplicate title (only if title is being updated)
        if data.title is not None:
            duplicate_title = await self.repo.find_job_by_title(data.title, company_id)

            if duplicate_title and duplicate_title.job_id != job_id:
                logger.warning(f"Service: Update failed. Job already exists with title: {data.title}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Job already exists with title."
                )
        

        update_dict = data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            setattr(valid_job, key, value)

        updated_job = await self.repo.update(valid_job)

        logger.info(f"Service: Job {updated_job.title} (ID: {updated_job.job_id}) updated successfully")

        return updated_job
    

    # Deleting a job post
    async def delete_job(self, job_id: int, company_id: int, manager_id: int) -> dict:

        logger.info(f"Service: Manager {manager_id} deleting job: {job_id}")

        await get_and_validate_company_ownership(
            self.company_repo, 
            company_id, 
            manager_id
        )    

        valid_job = await get_and_validate_job_ownership(
            self.repo, 
            job_id, 
            company_id
        )

        await self.repo.delete(valid_job)

        logger.info(f"Service: Job {valid_job.title} (ID: {valid_job.job_id}) deleted successfully")

        return {"message": "job deleted successfully"}
    

    # Finding a job post
    async def find_job(self, job_id: int, company_id: int, manager_id: int) -> JobPost:

        logger.info(f"Service: Manager {manager_id} fetching job: {job_id}")

        await get_and_validate_company_ownership(
            self.company_repo, 
            company_id, 
            manager_id
        )    

        valid_job = await get_and_validate_job_ownership(
            self.repo, 
            job_id, 
            company_id
        )

        logger.info(f"Service: Successfully found job: {job_id}")

        return valid_job
    

    # Finding all jobs for a company
    async def find_all_jobs(
        self,
        company_id: int,
        manager_id: int,
        skip: int = 0,
        limit: int = 10
    ) -> list[JobPost]:
        
        logger.info(f"Service: Manager {manager_id} fetching all jobs for company: {company_id}")

        await get_and_validate_company_ownership(self.company_repo, company_id, manager_id)

        jobs = await self.repo.find_all_jobs_by_company_id(company_id, skip=skip, limit=limit)

        logger.info(f"Service: Successfully found {len(jobs)} jobs for company: {company_id}")
        return jobs
    

    # Finding a job by title
    async def find_job_by_title(self, title: str, company_id: int) -> JobPost | None:

        logger.info(f"Service: Attempting to find a job with title: {title}")

        job = await self.repo.find_job_by_title(title, company_id)

        logger.info(f"Service: Successfully found a job with title: {title}")

        return job


    # Finding all active jobs for employees
    async def get_all_active_jobs(self, skip: int = 0, limit: int = 10) -> list[JobPost]:
        logger.info(f"Service: Fetching active jobs with skip={skip} limit={limit}")
        return await self.repo.find_all_active_jobs(skip, limit)


        