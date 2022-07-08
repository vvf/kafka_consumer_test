import pytest
from asynctest import patch


@pytest.mark.asyncio
@pytest.fixture
async def db():
    from models.base import init_session, Model
    asession = init_session()
    async with asession() as session:
        async with session.begin():
            conn = await session.connection()
            # in real life here replace to alembic upgrade and downgrade
            await conn.run_sync(Model.metadata.drop_all)
            await conn.run_sync(Model.metadata.create_all)
        with patch("models.base.db_session_context") as db_ctx_var:
            db_ctx_var.get.return_value = session
            yield session
        await session.rollback()
