from typing import TYPE_CHECKING, Annotated
from fastapi import APIRouter, Depends, HTTPException, status


from app.modules.companies.company_schema import CompanyCreate, CompanyUpdate
from app.api.dependencies import get_current_user, company_service_dependency


if TYPE_CHECKING:
    from app.modules.users.user_model import User
    

# --------------------------------------------------------------------------------------------------------------- #


router = APIRouter(prefix="/companies", tags=["Companies"])

# Current User Dependency
current_user = Annotated["User", Depends(get_current_user)]


# -------- Create Company Router -------- #
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    service: company_service_dependency,
    active_user: current_user
):
    
    if active_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can create companies",
        )

    return await service.create_company(data=data, manager_id=active_user.user_id)


# --------- Update Company Router --------- #
@router.patch("/{company_id}", status_code=status.HTTP_200_OK)
async def update_company(
    data: CompanyUpdate,
    service: company_service_dependency,
    active_user: current_user,
    company_id: int 
):

    return await service.update_company(
        data=data, 
        company_id=company_id, 
        manager_id=active_user.user_id
    )


# --------- Delete Company Router --------- #
@router.delete("/{company_id}", status_code=status.HTTP_200_OK)
async def delete_company(
    service: company_service_dependency,
    active_user: current_user,
    company_id: int
):

    return await service.delete_company(company_id=company_id, manager_id=active_user.user_id)


# --------- Find Company Router --------- #
@router.get("/{company_id}", status_code=status.HTTP_200_OK)
async def find_company(
    service: company_service_dependency,
    active_user: current_user,
    company_id: int 
):

    return await service.find_company(company_id=company_id, manager_id=active_user.user_id)


# --------- Find All Companies Router --------- #
@router.get("/", status_code=status.HTTP_200_OK)
async def find_all_companies(
    service: company_service_dependency,
    active_user: current_user
):

    return await service.find_all_companies(manager_id=active_user.user_id)
    