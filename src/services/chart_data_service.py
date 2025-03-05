from src.models import PeriodEntity
from src.repositories import PeriodRepositoryService


class ChartDataService:
    def __init__(self, period_service: PeriodRepositoryService):
        self.period_service = period_service

    async def get_last_period(self) -> PeriodEntity:
        return await self.period_service.get_one()