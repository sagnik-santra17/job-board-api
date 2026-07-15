import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.companies.company_model import Companies


# ------------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


class CompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    # Creating a company
    async def create(self, company: Companies) -> Companies:

        logger.info(f"Database: Attempting to insert new company with name: {company.company_name}")
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        logger.info(f"Database: Successfully created a company with company id: {company.company_id}")
        return company


    # Updating a company
    async def update(self, company: Companies) -> Companies:

        logger.info(f"Database: Attempting to update a company with company id: {company.company_id}")
        self.db.add(company)
        await self.db.commit()
        await self.db.refresh(company)
        logger.info(f"Database: Successfully updated a company with company id: {company.company_id}")
        return company


    # Deleting a company
    async def delete(self, company: Companies) -> None:

        logger.info(f"Database: Attempting to delete a company with company id: {company.company_id}")
        await self.db.delete(company)
        await self.db.commit()
        logger.info(f"Database: Successfully deleted a company with company id: {company.company_id}")


    # Finding a company by id
    async def find_company_by_id(self, company_id: int) -> Companies | None:

        logger.info(f"Database: Attempting to find a company with company id: {company_id}")
        query = select(Companies).where(Companies.company_id == company_id)
        results = await self.db.execute(query)
        company = results.scalar_one_or_none()

        if not company:
            logger.warning(f"Database: No company with company id: {company_id}")
        return company


    # Finding companies by manager id – returns a list of companies managed by a manager
    async def find_companies_by_manager_id(self, manager_id: int) -> list[Companies] | None:

        logger.info(f"Database: Attempting to find companies by manager id: {manager_id}")
        query = select(Companies).where(Companies.manager_id == manager_id)
        results = await self.db.execute(query)
        companies = results.scalars().all()

        if not companies:
            logger.warning(f"Database: No companies with manager id: {manager_id}")
            return None
        return companies


    # Find company by name (for duplicate check)
    async def find_company_by_name(self, company_name: str) -> Companies | None:

        logger.info(f"Database: Attempting to find a company with name: {company_name}")
        query = select(Companies).where(Companies.company_name == company_name)
        results = await self.db.execute(query)
        company = results.scalar_one_or_none()

        if not company:
            logger.warning(f"Database: No company with name: {company_name}")
        return company


    # Find company by email (for duplicate check during updates)
    async def find_company_by_email(self, company_email: str) -> Companies | None:
        
        logger.info(f"Database: Attempting to find a company with email: {company_email}")
        query = select(Companies).where(Companies.company_email == company_email)
        results = await self.db.execute(query)
        company = results.scalar_one_or_none()

        if not company:
            logger.warning(f"Database: No company with email: {company_email}")
        return company