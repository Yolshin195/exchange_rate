from arq import cron
from arq.connections import RedisSettings

from src.db import sqlalchemy_config
from src.models import PeriodEntity
from src.repositories import PeriodRepositoryService
from src.tasks.bybit import BybitService
from src.settings import settings

REDIS_SETTINGS = RedisSettings(host=settings.redis.host, port=settings.redis.port)


async def bybit_task(ctx):
    async with sqlalchemy_config.get_session() as session:
        await BybitService.get_instance(session)()


async def print_config_task(ctx):
    print('Test task')
    print(ctx)
    print(settings)


async def test_bd(ctx):
    async with sqlalchemy_config.get_session() as session:
        server = PeriodRepositoryService(session=session)
        await server.create(PeriodEntity(
            min=10,
            max=20,
            average=15,
        ), auto_commit=True)
        print(await server.get_last_n_period())


class WorkerSettings:
    cron_jobs = [
        cron("src.tasks.arq_settings.print_config_task"),
        cron("src.tasks.arq_settings.bybit_task"),
        cron("src.tasks.arq_settings.test_bd"),
    ]
    redis_settings = REDIS_SETTINGS
