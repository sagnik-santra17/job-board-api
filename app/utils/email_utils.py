import logging


# ------------------------------------------------------------------------------------------------------------------- #


# This will be replaced with the actual email sending logic, email service integration and actual email template


logger = logging.getLogger(__name__)


def send_email_notification(employee_email: str, job_title: str, company_name: str) -> None:

    # Stimulating the email sending process with logger
    logger.info(
        f"[MOCK EMAIL] To: {employee_email} | "
        f"Subject: Your application for '{job_title}' at {company_name} has been accepted!"
    )

