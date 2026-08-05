import logging
from typing import TYPE_CHECKING, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
import redis.asyncio as aioredis


from app.core.database import get_db
from app.core.config import settings
from app.utils.user_utils import invalid_credentials


if TYPE_CHECKING:
    from app.modules.users.user_service import UserService
    from app.modules.companies.company_service import CompanyService
    from app.modules.jobs.job_service import JobService
    from app.modules.applications.application_service import ApplicationService
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


# ------- Job dependency service injection -------- #
def get_job_service(db: db_dependency) -> "JobService":

    from app.modules.jobs.job_repository import JobRepository
    from app.modules.jobs.job_service import JobService
    from app.modules.companies.company_repository import CompanyRepository

    job_repo = JobRepository(db)
    company_repo = CompanyRepository(db)
    return JobService(job_repo, company_repo)

job_service_dependency = Annotated["JobService", Depends(get_job_service)]


# ------- Application dependency service injection -------- #
def get_application_service(db: db_dependency) -> "ApplicationService":

    from app.modules.applications.application_repository import ApplicationRepository
    from app.modules.applications.application_service import ApplicationService
    from app.modules.jobs.job_repository import JobRepository
    from app.modules.companies.company_repository import CompanyRepository
    from app.modules.users.user_repository import UserRepository

    application_repo = ApplicationRepository(db)
    job_repo = JobRepository(db)
    company_repo = CompanyRepository(db)
    user_repo = UserRepository(db)
    return ApplicationService(application_repo, job_repo, company_repo, user_repo)

application_service_dependency = Annotated["ApplicationService", Depends(get_application_service)]



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



# ------------- Rate Limiting Tool ------------ #

# Creating Redis client
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)

# Reusable class for rate limiting
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check_rate_limit(self, user_id: int | str):

        # Creating a unique key for this specific user in Redis
        key = f"rate_limit:user:{user_id}"

        # If the key doesn't exist yet, Redis automatically creates it at 1
        current_request = await redis_client.incr(key)

        if current_request == 1:
            # Uses the custom seconds we passed in
            await redis_client.expire(key, self.window_seconds)

        # If the counter goes past our limit (max_requests), block the request
        if current_request > self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many applications. Please wait a minute."
            )
