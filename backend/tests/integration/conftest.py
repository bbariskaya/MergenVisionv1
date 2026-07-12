import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mergenvision.config.settings import Settings

if not os.environ.get("MERGENVISION_DATABASE_URL"):
    pytest.skip("MERGENVISION_DATABASE_URL not set; skipping integration tests", allow_module_level=True)


@pytest_asyncio.fixture
async def db_engine():
    settings = Settings()
    engine = create_async_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine) -> AsyncSession:
    factory = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as s:
        yield s
        await s.rollback()
