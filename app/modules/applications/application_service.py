import logging
from fastapi import HTTPException, status


from app.modules.applications.application_model import JobApplication
from app.modules.applications.application_repository import ApplicationRepository
from app.modules.applications.application_schema import CreateApplication, UpdateApplication
from app.modules.companies.company_repository import CompanyRepository
from app.modules.jobs.job_repository import JobRepository
from app.utils.application_utils import validate_application_employee_ownership, validate_application_id_exists
from app.utils.company_utils import get_and_validate_company_ownership
from app.utils.job_utils import validate_job_id_exists



# ------------------------------------------------------------------------------------------------------------------ #


logger = logging.getLogger(__name__)


class ApplicationService:
    def __init__(
        self, 
        repo: ApplicationRepository,
        job_repo: JobRepository,
        company_repo: CompanyRepository
    ):
        self.repo = repo
        self.job_repo = job_repo
        self.company_repo = company_repo


    # Creating an application
    async def create_application(self, data: CreateApplication, job_id: int, employee_id: int) -> JobApplication:
        
        logger.info(f"Service: Employee {employee_id} applying to job {job_id}")

        # Verify job exists
        job = await self.job_repo.find_job_by_id(job_id)
        if not job:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, 
                "Job not found"
            )

        # Check for duplicate application
        existing = await self.repo.find_application_by_job_id_and_employee_id(job_id, employee_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already applied for this job"
            )

        # Create the application object
        new_application = JobApplication(
            **data.model_dump(),  # only contains status and cover_letter
            employee_id=employee_id,
            job_id=job_id
        )

        return await self.repo.create(new_application)


    # Updating an application
    async def update_application(
        self,
        application_id: int,
        data: UpdateApplication,
        employee_id: int | None = None,
        manager_id: int | None = None
) -> JobApplication:

        logger.info(
            f"Service: Attempting to update an application with application id: {application_id}"
        )

        # Fetch and validate the application exists
        application = await self.repo.find_application_by_id(application_id)
        valid_application = validate_application_id_exists(application)

        # Prepare the update dictionary (only fields that were sent)
        update_dict = data.model_dump(exclude_unset=True)

        # If neither employee_id or manager_id is provided, raise an error
        if employee_id is None and manager_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either employee_id or manager_id must be provided"
            )

        # If the employee is updating they can only update the cover letter
        if employee_id is not None:
            if valid_application.employee_id != employee_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to update this application"
                )

            # Check that only cover_letter is being updated
            for key in update_dict:
                if key != "cover_letter":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Employee can only update the cover letter"
                    )


        # If manager is updating, they must own the job's company and can only change status
        if manager_id is not None:

            # Get the job to verify ownership
            job = await self.job_repo.find_job_by_id(valid_application.job_id)
            valid_job = validate_job_id_exists(job)

            # Get the company to verify ownership
            company = await self.company_repo.find_company_by_id(valid_job.company_id)
            await get_and_validate_company_ownership(self.company_repo, company.company_id, manager_id)

            # Check that only status is being updated
            for key in update_dict:
                if key != "status":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Manager can only update the status"
                    )

        # Apply updates to the object
        for key, value in update_dict.items():
            setattr(valid_application, key, value)

        # Save changes
        updated_application = await self.repo.update(valid_application)
        logger.info(f"Service: Successfully updated application {application_id}")

        return updated_application


    # Deleting application
    async def delete_application(self, application_id: int, employee_id: int) -> None:

        logger.info(f"Service: Employee {employee_id} deleting application {application_id}")

        application = await self.repo.find_application_by_id(application_id)
        valid_application = validate_application_id_exists(application)

        authorized_application = validate_application_employee_ownership(valid_application, employee_id)

        await self.repo.delete(authorized_application)
        logger.info(f"Service: Successfully deleted application {application_id}")


    # Find application by id for employees
    async def get_application_by_id_for_employee(self, application_id: int, employee_id: int) -> JobApplication:

        logger.info(f"Service: Attempting to find an application with application id: {application_id}")

        application = await self.repo.find_application_by_id(application_id)
        valid_application = validate_application_id_exists(application)

        validate_application_employee_ownership(valid_application, employee_id)

        logger.info(f"Service: Successfully found an application with application id: {application_id}")

        return valid_application


    # Find application by id for managers
    async def get_application_by_id_for_manager(self, application_id: int, manager_id: int) -> JobApplication:

        logger.info(f"Service: Attempting to find an application with application id: {application_id}")

        application = await self.repo.find_application_by_id(application_id)
        valid_application = validate_application_id_exists(application)

        job = await self.job_repo.find_job_by_id(valid_application.job_id)
        valid_job = validate_job_id_exists(job)

        await get_and_validate_company_ownership(self.company_repo, valid_job.company_id, manager_id)

        logger.info(f"Service: Successfully found an application with application id: {application_id}")

        return valid_application


    # Look for all the applications for a specific employee
    async def get_all_applications_by_employee_id(self, employee_id: int) -> list[JobApplication]:

        logger.info(f"Service: Attempting to find applications by employee id: {employee_id}")

        applications = await self.repo.find_all_applications_by_employee_id(employee_id)

        logger.info(f"Service: Successfully found applications by employee id: {employee_id}")

        return applications


    # Look for all the applications for a specific manager
    async def get_all_applications_by_manager_id(self, manager_id: int) -> list[JobApplication]:

        logger.info(f"Service: Attempting to find applications by manager id: {manager_id}")

        # Get all companies owend by a manager
        companies = await self.company_repo.find_companies_by_manager_id(manager_id)

        if not companies:
            return []

        # Get all jobs created by those companies
        jobs = []

        for company in companies:
            jobs.extend(await self.job_repo.find_all_jobs_by_company_id(company.company_id))

        if not jobs:
            return []

        # Get all applications for each job
        applications = []

        for job in jobs:
            applications.extend(await self.repo.find_all_applications_by_job_id(job.job_id))

        logger.info(f"Service: Successfully found applications by manager id: {manager_id}")

        return applications


    # Find all the application according to their status
    async def get_all_applications_by_status(self, status: str, manager_id: int) -> list[JobApplication]:

        logger.info(f"Service: Attempting to find applications by status: {status}")

        applications = await self.get_all_applications_by_manager_id(manager_id=manager_id)

        # Filtering the applications by status
        filtered_applications = [application for application in applications if application.status == status]

        logger.info(f"Service: Found {len(filtered_applications)} applications by status: {status}")

        return filtered_applications


    # Get application by job id for managers
    async def get_applications_by_job_id_for_manager(self, job_id: int, manager_id: int) -> list[JobApplication]:
    
        logger.info(f"Service: Manager {manager_id} fetching applications for job {job_id}")

        # Retrieve the job to get its company_id
        job = await self.job_repo.find_job_by_id(job_id)
        valid_job = validate_job_id_exists(job)

        # Fetch the company that owns this job
        company = await self.company_repo.find_company_by_id(valid_job.company_id)

        # Verify the logged-in manager owns that company
        await get_and_validate_company_ownership(self.company_repo, company.company_id, manager_id)

        logger.info(f"Service: Successfully found applications for job {job_id}")

        return await self.repo.find_all_applications_by_job_id(job_id)





        
        
        

         


    