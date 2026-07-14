import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


from app.core.database import get_db
from app.main import app
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from app.core.database import Base

# ------------------------------------------------------------------------------------------------------------ #

# Use a separate SQLite database for testing 
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_database.db"


# Create async engine for the test database
test_async_engine: AsyncEngine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}   # -> Needed for SQLite
)


# Session factory for tests
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


# ---------- Fixtures ---------- #

# session-scoped: set up and tear down database schema once for all tests
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables before tests run, drop them after all tests finish."""
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# function-scoped: each test gets a fresh database session with a transaction
@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database):
    async with TestAsyncSessionLocal() as session:
        await session.begin()          # start transaction manually
        yield session                  # test runs here
        await session.rollback()       # rollback after test


# function-scoped: HTTP client with the test app and override database dependency
@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Provide an async HTTP client that uses the test database session."""

    # Override the dependency that returns the DB session
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db

    # Create the async client with ASGI transport (no actual network)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    # Clean up overrides after the test
    app.dependency_overrides.clear()