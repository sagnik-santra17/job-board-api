from typing import TYPE_CHECKING, Annotated
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm


from app.api.dependencies import get_current_user, user_service_dependency
from app.modules.users.user_schema import UserCreate, UserDelete, UserLogin, UserResponse, UserUpdate


if TYPE_CHECKING:
    from app.modules.users.user_model import User


# --------------------------------------------------------------------------------------------------------------- #


router = APIRouter(prefix="/users", tags=["Users"])

# Current User Dependency
current_user = Annotated["User", Depends(get_current_user)]


#----------user sign up router--------------#
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    service: user_service_dependency,
):
    new_user =  await service.create_user(data)
    return new_user


#--------------user log in router-----------#
@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    service: user_service_dependency,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user_login_data = UserLogin(
        username=form_data.username,
        password=form_data.password,
    )
    return await service.user_login(user_login_data)


#-------------user delete router------------#
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    data: UserDelete,
    service: user_service_dependency,
    active_user: current_user
):
    await service.user_delete(user_id=active_user.user_id, delete_data=data)
    return {"detail": "User account deleted successfully"}


#-------------user update router------------#
@router.patch("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    service: user_service_dependency,
    active_user: current_user,
    data: UserUpdate
):
   updated_user = await service.user_update(data=data, user_id=active_user.user_id)
   return updated_user


#-------------view user details router------------#
@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def view_user_details(
    service: user_service_dependency,
    active_user: current_user
):
    return await service.check_user_profile(user_id=active_user.user_id)


