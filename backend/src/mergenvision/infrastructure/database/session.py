from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def make_engine(database_url: str, *, pool_pre_ping: bool = True) -> AsyncEngine:
    return create_async_engine(
        database_url,
        pool_pre_ping=pool_pre_ping,
        future=True,
    )


def make_session_factory(
    engine: AsyncEngine,
    *,
    expire_on_commit: bool = False,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=expire_on_commit,
    )
