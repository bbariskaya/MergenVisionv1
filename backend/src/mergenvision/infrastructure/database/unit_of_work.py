from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mergenvision.infrastructure.database import repositories as repos
from mergenvision.ports import unit_of_work


class PostgresUnitOfWork(unit_of_work.UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> PostgresUnitOfWork:
        self._session = self._session_factory()
        self.person = repos.PostgresPersonRepository(self._session)
        self.face_identity = repos.PostgresFaceIdentityRepository(self._session)
        self.inference_profile = repos.PostgresInferenceProfileRepository(self._session)
        self.process_record = repos.PostgresProcessRecordRepository(self._session)
        self.person_photo = repos.PostgresPersonPhotoRepository(self._session)
        self.face_sample = repos.PostgresFaceSampleRepository(self._session)
        self.recognition_result = repos.PostgresRecognitionResultRepository(self._session)
        self.process_event = repos.PostgresProcessEventRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        try:
            if exc_val is not None:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active")
        await self._session.commit()

    async def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active")
        await self._session.rollback()
