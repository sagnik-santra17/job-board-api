import logging
from fastapi import HTTPException, status


from app.core.security import get_password_hash, verify_password, create_access_token
from app.modules.users.user_model import User
from app.modules.users.user_repository import UserRepository
from app.modules.users.user_schema import UserCreate, UserLogin, UserUpdate, UserDelete
from app.utils.user_utils import validate_username_check, validate_email_check, invalid_credentials, \
    validate_user_id_exists


# --------------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo


    #----------User sign up/creating a new user----------#
    async def create_user(self, data: UserCreate) -> User:
        logger.info(f"Service: Processing registration request for username: {data.username}")
        username = await self.repo.find_user_by_username(data.username)
        validate_username_check(username, data.username)

        logger.info(f"Service: Processing registration request for email: {data.email}")
        email = await self.repo.find_user_by_email(data.email)
        validate_email_check(email, data.email)

        hashed_password = get_password_hash(data.password)

        user_dict = data.model_dump(exclude={"password", "confirm_password"})

        new_user = User(
            **user_dict,
            hashed_password=hashed_password
        )

        logger.info(f"Service: Validation passed. Sending new user data to database layer.")
        return await self.repo.create(new_user)


    #----------login/sign in----------#
    async def user_login(self, login_data: UserLogin) -> dict[str, str]:
        logger.info(f"Service: Processing login request for username: {login_data.username}")
        valid_user = await self.repo.find_user_by_identifier(login_data.username)

        if valid_user is None:
            logger.warning(f"Service: Login failed. Identifier not found: {login_data.username}")
            invalid_credentials()
        if not verify_password(login_data.password, valid_user.hashed_password):
            logger.warning(f"Service: Login failed. Password incorrect for identifier: {login_data.username}")
            invalid_credentials()

        access_token = create_access_token(data={"sub": str(valid_user.user_id)})
        logger.info(f"Service: Login successful. Access token generated for user id: {valid_user.user_id}")

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }


    #----------User update----------#
    async def user_update(self, data: UserUpdate, user_id: int) -> User:
        logger.info(f"Service: Processing update request for user id: {user_id}")
        existing_user = await self.repo.find_user_by_user_id(user_id)
        valid_user = validate_user_id_exists(existing_user)

        if not verify_password(data.current_password, valid_user.hashed_password):
            logger.warning(f"Service: Update failed. Incorrect password entered for user ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect current password."
            )

        # Checking if the new username already exists
        if data.username:
            duplicate_user = await self.repo.find_user_by_username(data.username)
            if duplicate_user and duplicate_user.user_id != user_id:
                logger.warning(f"Service: Update failed. User already exists with username: {data.username}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already exists with username."
                )

        # Checking if the new email already exists
        if data.email:
            duplicate_user = await self.repo.find_user_by_email(data.email)
            if duplicate_user and duplicate_user.user_id != user_id:
                logger.warning(f"Service: Update failed. User already exists with email: {data.email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already exists with email."
                )

        update_data = data.model_dump(
            exclude_unset=True,
            exclude={"confirm_password", "current_password"}
        )

        if "password" in update_data:
            logger.info(f"Service: User ID {user_id} is changing their password. Hashing new password.")
            new_password = update_data.pop("password")
            update_data["hashed_password"] = get_password_hash(new_password)

        for key, value in update_data.items():
            setattr(valid_user, key, value)

        logger.info(f"Service: Sending updated fields to database layer for user ID: {user_id}")
        return await self.repo.update(valid_user)


    #----------delete user----------#
    async def user_delete(self, user_id: int, delete_data: UserDelete) -> None:
        logger.info(f"Service: Processing delete request for user id: {user_id}")
        existing_user = await self.repo.find_user_by_user_id(user_id)
        valid_user = validate_user_id_exists(existing_user)

        if not verify_password(delete_data.password, valid_user.hashed_password):
            logger.warning(f"Service: Delete failed. Password incorrect")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password. Account deletion aborted."
            )
        await self.repo.delete(valid_user)
        logger.info(f"Service: Sending deletion confirmation to database layer for user ID: {user_id}")
        return None


    #--------------get user data----------------#
    async def check_user_profile(self, user_id: int) -> User:
        logger.info(f"Service: Processing profile request for user id: {user_id}")
        existing_user = await self.repo.find_user_by_user_id(user_id)
        valid_user = validate_user_id_exists(existing_user)

        logger.info(f"Service: Profile successfully retrieved for user ID: {user_id}")
        return valid_user