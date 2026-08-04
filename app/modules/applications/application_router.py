from turtle import st
from typing import TYPE_CHECKING, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks


from app.api.dependencies import get_current_user, application_service_dependency
from app.modules.applications.application_schema import ApplicationResponse, CreateApplication, EmployeeApplicationResponse, UpdateApplication
from app.utils.email_utils import send_email_notification


if TYPE_CHECKING:
    from app.modules.users.user_model import User
    

# ---------------------------------------------------------------------------------------------------------------------- #


router = APIRouter(prefix="/jobs/{job_id}/applications", tags=["Applications"])


# Current User Dependency
current_user = Annotated["User", Depends(get_current_user)]


# Create application router
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_application(
    data: CreateApplication,
    service: application_service_dependency,
    active_user: current_user,
    job_id: int
):

    # Check if the user is an employee
    if active_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can apply for jobs",
        )

    return await service.create_application(
        data=data,
        job_id=job_id,
        employee_id=active_user.user_id
    )


# Update application router
@router.patch("/{application_id}", status_code=status.HTTP_200_OK)
async def update_application(
    data: UpdateApplication,
    service: application_service_dependency,
    active_user: current_user,
    background_tasks: BackgroundTasks,
    application_id: int,
):
    
    if active_user.role == "employee":
        app = await service.update_application(
            application_id, data, employee_id=active_user.user_id
        )
        return EmployeeApplicationResponse.model_validate(app)  #-> employee schema
    
    elif active_user.role == "manager":
        app = await service.update_application(
            application_id, data, manager_id=active_user.user_id
        )

        if data.status == "accepted":

            employee = await service.user_repo.find_user_by_user_id(app.employee_id)
            job = await service.job_repo.find_job_by_id(app.job_id)
            company = await service.company_repo.find_company_by_id(job.company_id)

            # Send email to employee with background task
            background_tasks.add_task(
                send_email_notification,
                employee_email=employee.email,
                job_title=job.title,
                company_name=company.company_name
            )
            
        return ApplicationResponse.model_validate(app) # -> full schema
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid role"
        )


# Delete application router
@router.delete("/{application_id}", status_code=status.HTTP_200_OK)
async def delete_application(
    service: application_service_dependency,
    active_user: current_user,
    application_id: int
):

    if active_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees can delete their own applications",
        )

    await service.delete_application(
        application_id=application_id, 
        employee_id=active_user.user_id
    )

    return {"detail": "Application deleted successfully"} 


# Finding a single application router
@router.get("/{application_id}", status_code=status.HTTP_200_OK)
async def get_application_by_id(
    service: application_service_dependency,
    active_user: current_user,
    application_id: int,
):
    if active_user.role == "employee":
        app = await service.get_application_by_id_for_employee(application_id, active_user.user_id)
        return EmployeeApplicationResponse.model_validate(app) # -> uses employee schema
    
    elif active_user.role == "manager":
        app = await service.get_application_by_id_for_manager(application_id, active_user.user_id)
        return ApplicationResponse.model_validate(app) # -> uses full schema
    
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid role"
        )


# Finding all application router
@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_applications(
    service: application_service_dependency,
    active_user: current_user,
):
    if active_user.role == "employee":
        apps = await service.get_all_applications_by_employee_id(active_user.user_id)
        return [EmployeeApplicationResponse.model_validate(app) for app in apps]
    
    elif active_user.role == "manager":
        return await service.get_all_applications_by_manager_id(manager_id=active_user.user_id)

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role for getting all applications",
        )


# Find all the application according to their status router
@router.get("/status/{status_value}", status_code=status.HTTP_200_OK, response_model=list[ApplicationResponse])
async def get_all_applications_by_status(
    service: application_service_dependency,
    active_user: current_user,
    status_value: str,
):
    
    if active_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can filter by status"
        )
    
    apps = await service.get_all_applications_by_status(status_value, active_user.user_id)
    return apps


# Find applications applied for a single job post
@router.get("/job/", status_code=status.HTTP_200_OK)
async def get_all_applications_by_job_id(
    service: application_service_dependency,
    active_user: current_user,
    job_id: int
):
    
    if active_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can get applications by job id",
        )

    return await service.get_applications_by_job_id_for_manager(
        job_id=job_id,
        manager_id=active_user.user_id
    )
    