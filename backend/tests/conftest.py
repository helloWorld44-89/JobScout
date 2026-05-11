import os

from passlib.context import CryptContext

# Set test env vars BEFORE any app imports so pydantic-settings picks them up
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
os.environ["APP_USERNAME"] = "testuser"
os.environ["APP_PASSWORD_HASH"] = _pwd.hash("testpassword")
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402

TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"

_engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    connect_args={"check_same_thread": False},
)
_SessionLocal = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def session(reset_db):  # noqa: ARG001
    async with _SessionLocal() as s:
        yield s


@pytest_asyncio.fixture
async def client(session: AsyncSession):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    res = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
