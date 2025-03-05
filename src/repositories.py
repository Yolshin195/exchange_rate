from typing import Iterable

from advanced_alchemy import filters
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy import select, Sequence

from src.models import OfferEntity, PeriodEntity


class OfficeRepository(SQLAlchemyAsyncRepository[OfferEntity]):
    model_type = OfferEntity


class OfficeRepositoryService(SQLAlchemyAsyncRepositoryService[OfferEntity]):
    repository_type = OfficeRepository


class PeriodRepository(SQLAlchemyAsyncRepository[PeriodEntity]):
    model_type = PeriodEntity


class PeriodRepositoryService(SQLAlchemyAsyncRepositoryService[PeriodEntity]):
    repository_type = PeriodRepository

    async def get_last_period(self) -> PeriodEntity:
        statement = select(PeriodEntity).order_by(PeriodEntity.created_at.desc()).limit(1)
        return await self.get_one(statement=statement)

    async def get_last_n_period(self, limit=100) -> Iterable[PeriodEntity]:
        limit_offset = filters.LimitOffset(limit=limit, offset=0)
        return await self.list(limit_offset)
