from typing import TYPE_CHECKING, Annotated
from fastapi import APIRouter, Depends, HTTPException, status


from app.api.dependencies import get_current_user, application_service_dependency
from app.modules.applications.application_schema import ApplicationResponse, CreateApplication, UpdateApplication


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
    application_id: int
):

    if active_user.role == "employee":
        return await service.update_application(
            data=data, 
            application_id=application_id, 
            employee_id=active_user.user_id
        )

    elif active_user.role == "manager":
        return await service.update_application(
            data=data, 
            application_id=application_id, 
            manager_id=active_user.user_id
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role for updating an application",
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

    return await service.delete_application(
        application_id=application_id, 
        employee_id=active_user.user_id
    )


# Finding a single application router
@router.get("/{application_id}", status_code=status.HTTP_200_OK)
async def get_application_by_id(
    service: application_service_dependency,
    active_user: current_user,
    application_id: int
):

    if active_user.role == "employee":
        return await service.get_application_by_id_for_employee(
            application_id=application_id, 
            employee_id=active_user.user_id
        )

    elif active_user.role == "manager":
        return await service.get_application_by_id_for_manager(
            application_id=application_id, 
            manager_id=active_user.user_id
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role for getting an application",
        )


# Finding all application router
@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_applications(
    service: application_service_dependency,
    active_user: current_user,
):
    if active_user.role == "employee":
        return await service.get_all_applications_by_employee_id(employee_id=active_user.user_id)
    
    elif active_user.role == "manager":
        return await service.get_all_applications_by_manager_id(manager_id=active_user.user_id)

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role for getting all applications",
        )


# Find all the application according to their status router
@router.get("/status/{status_value}", status_code=status.HTTP_200_OK)
async def get_all_applications_by_status(
    service: application_service_dependency,
    active_user: current_user,
    status_value: str,   # renamed to avoid shadowing fastapi.status
):
    if active_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can filter by status"
        )
    apps = await service.get_all_applications_by_status(status_value, active_user.user_id)
    return [ApplicationResponse.model_validate(app, from_attributes=True) for app in apps]


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
    