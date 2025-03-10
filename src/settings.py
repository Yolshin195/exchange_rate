import os
from enum import Enum

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

class EnvironmentEnum(str, Enum):
    local = "local"
    docker = "docker"


class RedisSettings(BaseModel):
    host: str
    port: int


class PostgresSettings(BaseModel):
    host: str
    port: int
    password: str
    user: str
    db: str

    @property
    def connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class ByBit(BaseModel):
    browser: str
    url: str


class Settings(BaseSettings):
    postgres: PostgresSettings
    redis: RedisSettings
    bybit: ByBit

    environment: str = os.getenv("ENVIRONMENT", EnvironmentEnum.local.value)
    env_file_testing: list[str] = (['.env.docker']
            if environment == EnvironmentEnum.docker.value
            else ['.env', '../.env']
    )
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_file=('.env.docker' if environment == EnvironmentEnum.docker.value else ['.env', '../.env'])
    )

settings = Settings()

environment: str = os.getenv("ENVIRONMENT", EnvironmentEnum.local.value)
print(environment, environment == EnvironmentEnum.docker.value)

print(f'{settings.model_config}')

if __name__ == "__main__":
    print(settings)
    print(settings.postgres)
    print(settings.redis)
