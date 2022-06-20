import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.database.deps import Base, get_async_session
from app.settings import Settings

settings = Settings.get()


@pytest.fixture(scope="function")
async def sync_engine():
    engine = create_engine(settings.test_sync_connection_url)
    yield engine


@pytest.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(settings.test_async_connection_url)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def session(async_engine) -> AsyncSession:
    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
def create_db(sync_engine):
    url = sync_engine.url

    if not database_exists(url):
        create_database(url)
        Base.metadata.create_all(bind=sync_engine)

    yield

    if database_exists(url):
        drop_database(url)


@pytest.fixture(scope="function")
async def client_factory(session):
    from app.main import app

    async def override_get_db():
        yield session

    app.dependency_overrides[get_async_session] = override_get_db

    class ClientFactory:
        @staticmethod
        def get() -> AsyncClient:
            return AsyncClient(
                app=app,
                base_url="http://testserver",
                headers={"Content-Type": "application/json"},
            )

    yield ClientFactory

    app.dependency_overrides[get_async_session] = get_async_session


@pytest.fixture(scope="function")
async def client(client_factory):
    client = client_factory.get()

    async with client:
        yield client
