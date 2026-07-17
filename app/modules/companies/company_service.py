import logging
from fastapi import HTTPException, status


from app.modules.companies.company_model import Companies
from app.modules.companies.company_repository import CompanyRepository
from app.modules.companies.company_schema import CompanyCreate, CompanyUpdate
from app.utils.company_utils import get_and_validate_company_ownership, valid_company_email_check, valid_company_name_check, validate_company_id_exists


# --------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)

class CompanyService:
    def __init__(self, repo: CompanyRepository):
        self.repo = repo


    # Creating a new company by validating manager role:
    async def create_company(self, data: CompanyCreate, manager_id: int) -> Companies:

        logger.info(f"Service: Manager {manager_id} creating company: {data.company_name}")


        # Chekcing if the company name already exists
        existing_name = await self.repo.find_company_by_name(data.company_name)
        valid_company_name_check(existing_name, data.company_name)


        # Checking if the company email already exists
        existing_email = await self.repo.find_company_by_email(data.company_email)
        valid_company_email_check(existing_email, data.company_email)
        

        company_dict = data.model_dump()
        company_dict["company_website"] = str(company_dict["company_website"]) if company_dict.get("company_website") else None
        
        new_company = Companies(**company_dict, manager_id=manager_id)


        created_company = await self.repo.create(new_company)

        logger.info(
            f"Service: Company {created_company.company_name} (ID: {created_company.company_id}) created successfully"
        )

        return created_company


    # Updating a company
    async def update_company(self, data: CompanyUpdate, company_id: int, manager_id: int) -> Companies:

        logger.info(f"Service: Manager {manager_id} updating company: {company_id}")

        valid_company = await get_and_validate_company_ownership(
            self.repo, company_id, manager_id
        )


        # Checking if the new company name already exists
        if data.company_name:
            duplicate_company = await self.repo.find_company_by_name(data.company_name)
            if duplicate_company and duplicate_company.company_id != company_id:
                logger.warning(f"Service: Update failed. Company already exists with name: {data.company_name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Company already exists with name."
                )   
            
        
        # Checking if the new company email already exists
        if data.company_email:
            duplicate_company = await self.repo.find_company_by_email(data.company_email)
            if duplicate_company and duplicate_company.company_id != company_id:
                logger.warning(f"Service: Update failed. Company already exists with email: {data.company_email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Company already exists with email."
                )   


        update_dict = data.model_dump(exclude_unset=True)
        update_dict["manager_id"] = manager_id

        for key, value in update_dict.items():
            setattr(valid_company, key, value)

        updated_company = await self.repo.update(valid_company)

        logger.info(
            f"Service: Company {updated_company.company_name} (ID: {updated_company.company_id}) updated successfully"
        )

        return updated_company
    

    # Delete a company
    async def delete_company(self, company_id: int, manager_id: int) -> dict:

        logger.info(f"Service: Manager {manager_id} deleting company: {company_id}")

        valid_company = await get_and_validate_company_ownership(
            self.repo, company_id, manager_id
        )

        await self.repo.delete(valid_company)

        logger.info(f"Service: Company {valid_company.company_name} (ID: {valid_company.company_id}) deleted successfully")

        return {"message": "company deleted successfully"}
    

    # Find a company
    async def find_company(self, company_id: int, manager_id: int) -> Companies:

        logger.info(f"Service: Manager {manager_id} fetching company {company_id}")

        valid_company = await get_and_validate_company_ownership(self.repo, company_id, manager_id)

        logger.info(f"Service: Successfully found company {company_id}")
        
        return valid_company
    

    # Find all companies created by a manager
    async def find_all_companies(self, manager_id: int) -> list[Companies] | None:

        logger.info(f"Service: Attempting to find all companies created by manager: {manager_id}")

        companies = await self.repo.find_companies_by_manager_id(manager_id)

        logger.info(f"Service: Successfully found all companies created by manager: {manager_id}")

        return companies