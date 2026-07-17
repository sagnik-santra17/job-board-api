import logging
from fastapi import HTTPException,status


from app.modules.companies.company_model import Companies


# ----------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


#--------checking if company_name already exists---------#
def valid_company_name_check(company: Companies | None, company_name: str) -> None:

    if company:
        logger.warning(f"Company creation failed: Company name {company_name}' is already taken.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Company name: {company_name} already in use"
        )
    

#--------checking if company_email already exists---------#
def valid_company_email_check(company: Companies | None, company_email: str) -> None:

    if company:
        logger.warning(f"Registration failed: email '{company_email}' is already taken.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Company email: {company_email} already in use"
        )
    

#--------checking if the entered company id is valid/if the company exists---------#
def validate_company_id_exists(company: Companies | None) -> Companies:

    if company is None:
        logger.warning("Company lookup failed: The requested company ID does not exist.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found with that company id"
        )
    return company



# -------- Getting and validating company ownership -------- #
def get_and_validate_company_ownership(repo, company_id: int, manager_id: int) -> Companies:

    company = repo.find_company_by_id(company_id)

    if company.manager_id != manager_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to update this company."
        )

    return company