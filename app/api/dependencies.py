import logging
from typing import TYPE_CHECKING, Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError



from app.core.database import get_db
from app.core.config import settings
from app.utils.user_utils import invalid_credentials


if TYPE_CHECKING:
    from app.modules.users.user_service import UserService
    from app.modules.companies.company_service import CompanyService
    from app.modules.users.user_model import User
    

# ----------------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


# ----------- Main Database Dependency ---------- #
db_dependency = Annotated[AsyncSession, Depends(get_db)]


#-------User dependency service injection--------#
def get_user_service(db: db_dependency) -> "UserService":
    from app.modules.users.user_repository import UserRepository
    from app.modules.users.user_service import UserService
    repo = UserRepository(db)
    return UserService(repo)

user_service_dependency = Annotated["UserService", Depends(get_user_service)]


# ------- Company dependency service injection -------- #
def get_company_service(db: db_dependency) -> "CompanyService":
    from app.modules.companies.company_service import CompanyService
    from app.modules.companies.company_repository import CompanyRepository
    repo = CompanyRepository(db)
    return CompanyService(repo)

company_service_dependency = Annotated["CompanyService", Depends(get_company_service)]








#-------Getting the current/logged in user------#
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        user_service: user_service_dependency
) -> "User":
    user_id = None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_data = payload.get("sub")
        if user_data is None:
            invalid_credentials()

        try:
            user_id = int(user_data)
        except ValueError:
            invalid_credentials()

    except ExpiredSignatureError:
        logger.warning("Security: Attempted access with an expired JWT token.")
        invalid_credentials()

    except JWTError:
        logger.warning("Security: Failed to decode JWT token. Invalid signature or format.")
        invalid_credentials()

    user = await user_service.repo.find_user_by_user_id(user_id)
    if user is None:
        logger.warning(f"Security: Token valid, but user ID {user_id} does not exist.")
        invalid_credentials()
    return user
