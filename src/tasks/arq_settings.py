from arq import cron
from arq.connections import RedisSettings

from src.db import sqlalchemy_config
from src.tasks.bybit import BybitService
from src.settings import settings

REDIS_SETTINGS = RedisSettings(host=settings.redis.host, port=settings.redis.port)


async def bybit_task(ctx):
    async with sqlalchemy_config.get_session() as session:
        await BybitService.get_instance(session)()


class WorkerSettings:
    cron_jobs = [
        cron("src.tasks.arq_settings.bybit_task")
    ]
    redis_settings = REDIS_SETTINGS
