import logging
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession


from app.modules.users.user_model import User


# ------------------------------------------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    
    #------Creating a new user--------#
    async def create(self, user: User) -> User:

        logger.info(f"Database: Attempting to insert new user with email: {user.email}")
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Database: Successfully created a user with user id: {user.user_id}")
        return user
    

    #--------Deleting a user---------#
    async def delete(self, user: User) -> None:
        logger.info(f"Database: Attempting to delete a user with user id: {user.user_id}")
        await self.db.delete(user)
        await self.db.commit()
        logger.info(f"Database: Successfully deleted a user with user id: {user.user_id}")


    #--------Updating user data---------#
    async def update(self, user: User) -> User:
        logger.info(f"Database: Attempting to update a user with user id: {user.user_id}")
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        logger.info(f"Database: Successfully updated a user with user id: {user.user_id}")
        return user
    

    #--------Find user with user id--------#
    async def find_user_by_user_id(self, user_id: int) -> User | None:
        logger.info(f"Database: Attempting to find a user with user id: {user_id}")
        query = select(User).where(User.user_id == user_id)
        results = await self.db.execute(query)
        user = results.scalar_one_or_none()

        if not user:
            logger.warning(f"Database: No user with user id: {user_id}")
        return user
    

    #--------Find user with identifier(username and email)--------#
    async def find_user_by_identifier(self, identifier: str) -> User | None:
        logger.info(f"Database: Attempting to find a user with username or email: {identifier}")
        query = select(User).where(
            or_(
                User.email == identifier,
                User.username == identifier,
            )
        )
        results = await self.db.execute(query)
        user = results.scalar_one_or_none()

        if not user:
            logger.warning(f"Database: No user with username or email: {identifier}")
        return user
    

    #--------Find user with email----------#
    async def find_user_by_email(self, email: str) -> User | None:
        logger.info(f"Database: Attempting to find a user with email: {email}")
        query = select(User).where(User.email == email)
        results = await self.db.execute(query)
        user = results.scalar_one_or_none()

        if not user:
            logger.warning(f"Database: No user with email: {email}")
        return user


    # --------Find user with username----------#
    async def find_user_by_username(self, username: str) -> User | None:
        logger.info(f"Database: Attempting to find a user with username: {username}")
        query = select(User).where(User.username == username)
        results = await self.db.execute(query)
        user = results.scalar_one_or_none()

        if not user:
            logger.warning(f"Database: No user with username: {username}")
        return user