import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from src import app
from src.db.main import get_session
from src.auth.dependencies import get_current_user
from src.db.models import User
import uuid
from datetime import datetime

# Use SQLite in memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session


def override_get_current_user():
    return User(
        uid=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash="hashed",
        role="member",
        is_verified=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


app.dependency_overrides[get_session] = override_get_session
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def session():
    async with TestingSessionLocal() as s:
        yield s