import asyncio
from advanced_alchemy.config import SQLAlchemyAsyncConfig, AsyncSessionConfig

from src.models import OfferEntity
from src.settings import settings


# Create a test config using SQLite
session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=settings.postgres.connection_string,
    session_config=session_config,
    create_all=True,
)


if __name__ == "__main__":
    async def main():
        async with sqlalchemy_config.get_engine().begin() as conn:
            await conn.run_sync(OfferEntity.metadata.create_all)

    asyncio.run(main())
