import asyncio
from pathlib import Path
from typing import AsyncGenerator, Any

from litestar import Litestar, get, websocket_stream
from litestar.di import Provide
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.template.config import TemplateConfig

from litestar.plugins.sqlalchemy import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import PeriodRepositoryService
from src.settings import settings, EnvironmentEnum

RESOURCE_LOCK = asyncio.Lock()

print(settings)
print(settings.environment == "docker")
print(settings.postgres.connection_string)
session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=settings.postgres.connection_string,
    session_config=session_config,
    create_all=True,
)
alchemy = SQLAlchemyPlugin(config=sqlalchemy_config)


async def provider_period_service(db_session: AsyncSession):
    return PeriodRepositoryService(session=db_session)


@get(
    path='/config'
)
async def get_config() -> dict[str, Any]:
    return settings.dict()


@get(
    path="/",
    dependencies={"service" : Provide(provider_period_service)}
)
async def hello_world(
    service: PeriodRepositoryService,
) -> Template:
    periods = await service.get_last_n_period()
    return Template(template_name="index.html.jinja2", context={
        'min_points': [period.min for period in periods],
        'max_points': [period.max for period in periods],
        'average_points': [period.average for period in periods],
    })


@websocket_stream(
    "/ping",
    dependencies={"service" : Provide(provider_period_service)},
)
async def ping(
    service: PeriodRepositoryService,
) -> AsyncGenerator[dict[str, Any], None]:
    while True:
        async with RESOURCE_LOCK:
            period = await service.get_last_period()
            yield {
                'min': period.min,
                'max': period.max,
                'average': period.average,
            }
        await asyncio.sleep(65)


app = Litestar(
    [hello_world, ping, get_config],
    plugins=[SQLAlchemyPlugin(config=sqlalchemy_config)],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
    pdb_on_exception=True
)
