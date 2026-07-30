import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.applications.application_model import JobApplication


# -------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


class ApplicationRepository:
    def __init__(self,  db: AsyncSession):
        self.db = db


    async def create(self, application: JobApplication) -> JobApplication:

        logger.info(f"Database: Attempting to insert new application with job id: {application.job_id} and employee id: {application.employee_id}")
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        logger.info(f"Database: Successfully created an application with application id: {application.application_id}")
        return application


    async def update(self, application: JobApplication) -> JobApplication:

        logger.info(f"Database: Attempting to update an application with application id: {application.application_id}")
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        logger.info(f"Database: Successfully updated an application with application id: {application.application_id}")
        return application


    async def delete(self, application: JobApplication) -> None:

        logger.info(f"Database: Attempting to delete an application with application id: {application.application_id}")
        await self.db.delete(application)
        await self.db.commit()
        logger.info(f"Database: Successfully deleted an application with application id: {application.application_id}")


    async def find_application_by_id(self, application_id: int) -> JobApplication | None:

        logger.info(f"Database: Attempting to find an application with application id: {application_id}")
        query = select(JobApplication).where(JobApplication.application_id == application_id)
        results = await self.db.execute(query)
        application = results.scalar_one_or_none()

        if not application:
            logger.warning(f"Database: No application with application id: {application_id}")
        return application


    async def find_all_applications_by_job_id(self, job_id: int) -> list[JobApplication]:

        logger.info(f"Database: Attempting to find applications by job id: {job_id}")
        query = select(JobApplication).where(JobApplication.job_id == job_id)
        results = await self.db.execute(query)
        applications = results.scalars().all()

        if not applications:
            logger.warning(f"Database: No applications with job id: {job_id}")
            return []
        return applications


    async def find_all_applications_by_employee_id(self, employee_id: int) -> list[JobApplication]:

        logger.info(f"Database: Attempting to find applications by employee id: {employee_id}")
        query = select(JobApplication).where(JobApplication.employee_id == employee_id)
        results = await self.db.execute(query)
        applications = results.scalars().all()

        if not applications:
            logger.warning(f"Database: No applications with employee id: {employee_id}")
            return []
        return applications


    async def find_all_applications_by_status(self, status: str) -> list[JobApplication]:

        logger.info(f"Database: Attempting to find applications by status: {status}")
        query = select(JobApplication).where(JobApplication.status == status)
        results = await self.db.execute(query)
        applications = results.scalars().all()

        if not applications:
            logger.warning(f"Database: No applications with status: {status}")
            return []
        return applications


    async def find_application_by_job_id_and_employee_id(self, job_id: int, employee_id: int) -> JobApplication | None:

        logger.info(f"Database: Attempting to find an application with job id: {job_id} and employee id: {employee_id}")

        query = select(JobApplication).where(
            JobApplication.job_id == job_id, JobApplication.employee_id == employee_id
        )

        results = await self.db.execute(query)
        application = results.scalar_one_or_none()

        if not application:
            logger.warning(f"Database: No application with job id: {job_id} and employee id: {employee_id}")
        return application
 

