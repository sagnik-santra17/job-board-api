import logging
from typing import Sequence
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.job_model import JobPost


# ------------------------------------------------------------------------------------------------------------------------ #


logger = logging.getLogger(__name__)


class JobRepository:
    def __init__(self,  db: AsyncSession):
        self.db = db


    async def create(self, job: JobPost) -> JobPost:

        logger.info(f"Database: Attempting to insert new job with title: {job.title}")
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        logger.info(f"Database: Successfully created a job with job id: {job.job_id}")
        return job 


    async def update(self, job: JobPost) -> JobPost:

        logger.info(f"Database: Attempting to update a job with job id: {job.job_id}")
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        logger.info(f"Database: Successfully updated a job with job id: {job.job_id}")
        return job
    

    async def delete(self, job: JobPost) -> None:

        logger.info(f"Database: Attempting to delete a job with job id: {job.job_id}")
        await self.db.delete(job)
        await self.db.commit()
        logger.info(f"Database: Successfully deleted a job with job id: {job.job_id}")


    async def find_job_by_id(self, job_id: int) -> JobPost | None:

        logger.info(f"Database: Attempting to find a job with job id: {job_id}")
        query = select(JobPost).where(JobPost.job_id == job_id)
        results = await self.db.execute(query)
        job = results.scalar_one_or_none()

        if not job:
            logger.warning(f"Database: No job with job id: {job_id}")
        return job
    

    async def find_all_jobs_by_company_id(
        self, 
        company_id: int, 
        skip: int = 0, 
        limit: int = 10
    ) -> Sequence[JobPost]:

        logger.info(f"Database: Attempting to find jobs by company id: {company_id}")
        query = (
            select(JobPost)
            .where(JobPost.company_id == company_id)
            .offset(skip)
            .limit(limit)
        )

        results = await self.db.execute(query)
        jobs = results.scalars().all()

        if not jobs:
            logger.warning(f"Database: No jobs with company id: {company_id}")
            return [] # -> Return an empty list if no jobs

        return jobs

        
    async def find_job_by_title(self, title: str, company_id: int) -> JobPost | None: # -> Adding company_id so duplicate jobs can't be found

        logger.info(f"Database: Attempting to find a job with title: {title}")
        query = select(JobPost).where(
            JobPost.title == title, 
            JobPost.company_id == company_id
        )
        results = await self.db.execute(query)
        job = results.scalar_one_or_none()

        if not job:
            logger.warning(f"Database: No job with title: {title}")
        return job


    # ---- NEW: Public endpoint for employees to browse active jobs ----
    async def find_all_active_jobs(self, skip: int = 0, limit: int = 10) -> Sequence[JobPost]:
        logger.info(f"Database: Fetching active jobs with skip={skip} limit={limit}")
        query = (
            select(JobPost)
            .where(JobPost.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(desc(JobPost.created_at))
        )
        results = await self.db.execute(query)
        jobs = results.scalars().all()
        logger.info(f"Database: Found {len(jobs)} active jobs")
        return jobs