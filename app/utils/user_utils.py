#global imports
import logging
from fastapi import HTTPException, status
#local imports
from app.modules.users.user_model import User

logger = logging.getLogger(__name__)

#--------checking if username already exists---------#
def validate_username_check(user: User | None, username: str) -> None:
    if user:
        logger.warning(f"Registration failed: Username '{username}' is already taken.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with username {username} already exists"
        )

#--------checking if email already exists---------#
def validate_email_check(user: User | None, email: str) -> None:
    if user:
        logger.warning(f"Registration failed: email '{email}' is already taken.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {email} already exists"
        )

#--------checking if the entered user id is valid---------#
def validate_user_id_exists(user: User | None) -> User | None:
    if user is None:
        logger.warning("User lookup failed: The requested user ID does not exist.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with that user id"
        )
    return user

#---------Error for invalid username or password-----------#
def invalid_credentials():
    logger.warning("Authentication failed: A user entered an incorrect username or password.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )