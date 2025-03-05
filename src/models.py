from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column


class PeriodEntity(UUIDAuditBase):
    __tablename__ = "period"

    min: Mapped[float]
    max: Mapped[float]
    average: Mapped[float]

    offers: Mapped[list["OfferEntity"]] = relationship(
        back_populates = "period"
    )


class OfferEntity(UUIDAuditBase):
    username: Mapped[str]  # Имя пользователя
    total_orders: Mapped[int]  # Исполненные заказы
    completion_rate: Mapped[float]  # Процент выполнения
    price: Mapped[float]  # Цена
    available_amount: Mapped[float]  # Доступное количество
    min_limit: Mapped[float]  # Минимальный лимит
    max_limit: Mapped[float]  # Максимальный лимит
    payment_methods: Mapped[str]  # Метод оплаты

    period_id: Mapped[UUID] = mapped_column(ForeignKey("period.id"))
    period: Mapped["PeriodEntity"] = relationship(back_populates="offers")
