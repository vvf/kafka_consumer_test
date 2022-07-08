import asyncio
import uuid
from contextvars import ContextVar
from typing import Awaitable, Callable

from sqlalchemy import Column, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import async_scoped_session, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

Model = declarative_base()

__async_session = None
db_session_context = ContextVar('db_session')


def get_session() -> AsyncSession:
    return db_session_context.get()


class SurrogatePK(object):
    """A mixin that adds a surrogate integer 'primary key' column named
    ``id`` to any declarative-mapped class.
    """
    __table_args__ = {'extend_existing': True}

    id = Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))

    @classmethod
    async def get_by_id(cls, _id):
        try:
            if isinstance(_id, uuid.UUID):
                uuid_id = _id
            elif isinstance(_id, (str, bytes)):
                uuid_id = uuid.UUID(_id)
            else:
                return None
        except ValueError:
            return None
        db_session = get_session()
        sql = select(cls).where(cls.id == uuid_id)
        query_result = await db_session.execute(sql)
        return next(query_result)


def init_session():
    global __async_session
    if __async_session is not None:
        return __async_session
    engine = create_async_engine(
        f"postgresql+asyncpg://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}"
        f"@{settings.DATABASE_HOST}/{settings.DATABASE_NAME}",
        # echo=True,
        pool_size=settings.KAFKA_MAX_RECORDS,
        max_overflow=1
    )

    # expire_on_commit=False will prevent attributes from being expired
    # after commit.
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    __async_session = async_session
    return async_session


async def run_with_db(coro):
    async_session_factory = init_session()

    session = async_scoped_session(async_session_factory, scopefunc=asyncio.current_task)
    db_session_context.set(session)
    if isinstance(coro, Awaitable):
        await coro
    elif isinstance(coro, Callable):
        await coro()
