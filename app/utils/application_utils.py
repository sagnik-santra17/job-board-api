from fastapi import HTTPException, status


from app.modules.applications.application_model import JobApplication


# ---------------------------------------------------------------------------------------------------------------- #


def validate_application_id_exists(application: JobApplication | None) -> JobApplication:

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    return application



def validate_application_employee_ownership(application: JobApplication, employee_id: int) -> JobApplication:
    if application.employee_id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this application"
        )
    return application