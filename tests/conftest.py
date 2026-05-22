import pytest
from pathlib import Path

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.main import app
from app.db.session import get_db

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(DATABASE_URL, future=True, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session


@pytest.fixture(autouse=True)
def override_get_db(test_session):
    async def _get_test_db():
        yield test_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def tmp_storage_path(tmp_path, monkeypatch):
    import app.services.storage_service as storage_service

    monkeypatch.setattr(storage_service.settings, "local_storage_path", tmp_path)
    return tmp_path
