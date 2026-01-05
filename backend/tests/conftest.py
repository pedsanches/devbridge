"""Pytest Configuration and Fixtures."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models.organization import Organization, PlanType
from app.models.organization_settings import OrganizationSettings
from app.models.user import User

# Test database URL (use a separate DB in production)
# For now used local dev DB but with transaction rollback
TEST_DATABASE_URL = str(settings.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")


@pytest.fixture
async def test_engine():
    """Create engine for test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Optional: Create tables if not exist (using migration is better usually)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for a test.
    Rolls back transaction at the end.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
    )
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async client with overridden DB dependency."""

    # Override get_db to use test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_org(db_session: AsyncSession) -> Organization:
    """Get or create a test organization."""
    from sqlalchemy import select

    result = await db_session.execute(select(Organization).where(Organization.slug == "test-org"))
    org = result.scalar_one_or_none()

    if not org:
        org = Organization(
            name="Test Org",
            slug="test-org",
            plan=PlanType.FREE,
        )
        db_session.add(org)
        await db_session.flush()

        # Add settings
        settings = OrganizationSettings(
            organization_id=org.id,
        )
        db_session.add(settings)
        await db_session.commit()
        await db_session.refresh(org)

    return org


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Get or create a test user."""
    from sqlalchemy import select

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email="test@example.com",
            name="Test User",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

    return user


@pytest.fixture
def authenticated_headers(test_user: User, test_org: Organization) -> dict[str, str]:
    """Get headers with valid JWT token."""
    access_token = create_access_token(data={"sub": str(test_user.id), "org_id": str(test_org.id)})
    return {"Authorization": f"Bearer {access_token}"}
