import asyncio
import re
from dataclasses import dataclass

import playwright.async_api
from playwright.async_api import async_playwright
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PeriodEntity
from src.repositories import OfficeRepositoryService, PeriodRepositoryService
from src.settings import settings


@dataclass
class Offer:
    username: str  # Имя пользователя
    total_orders: int  # Исполненные заказы
    completion_rate: float  # Процент выполнения
    price: float  # Цена
    available_amount: float  # Доступное количество
    min_limit: float  # Минимальный лимит
    max_limit: float  # Максимальный лимит
    payment_methods: str  # Метод оплаты


class OfferParser:
    def __init__(self):
        self.username: str | None = None  # Имя пользователя
        self.total_orders: int | None = None  # Исполненные заказы
        self.completion_rate: float | None = None  # Процент выполнения
        self.price: float | None = None  # Цена
        self.available_amount: float | None = None  # Доступное количество
        self.min_limit: float | None = None  # Минимальный лимит
        self.max_limit: float | None = None  # Максимальный лимит
        self.payment_methods: str | None = None

    async def parse(self, row) -> Offer | None:
        td_list = await row.query_selector_all('td')
        if len(td_list) == 0:
            return None

        # Парсим ownt_list (имя пользователя, исполненные заказы, процент выполнения)
        ownt_list = await td_list[0].query_selector_all('span')
        if len(ownt_list) >= 4:
            self.username = await ownt_list[0].text_content()
            self.total_orders = int(
                (await ownt_list[1].text_content()).replace(' исполнено', '').replace(',', '').strip())
            self.completion_rate = float((await ownt_list[3].text_content()).replace('%', '').strip())

        # Парсим price_list (цена)
        price_list = await td_list[1].query_selector_all('span')
        if len(price_list) > 0:
            price_text = await price_list[0].text_content()
            price_text, currency = price_text.replace('\xa0', ' ').split(' ')
            self.price = float(price_text.replace(',', '.').strip())

        # Парсим limits_list (доступное количество, минимальный и максимальный лимиты)
        limits_list = await td_list[2].query_selector_all('.ql-value')
        if len(limits_list) >= 2:
            available_amount_text = await limits_list[0].text_content()
            available_amount_text, available_currency = available_amount_text.replace('\xa0', ' ').split(' ')
            self.available_amount = float(available_amount_text.replace(',', '.').strip())
            limits_text = await limits_list[1].text_content()
            min_limit, max_limit = limits_text.split('\xa0~\xa0')
            max_limit, limit_currency = self.parse_currency(max_limit)
            self.min_limit = float(min_limit.replace('\xa0', ' ').replace(' ', '').replace(',', '.').strip())
            self.max_limit = max_limit

        # Парсим payment_method_list (способы оплаты)
        payment_method_list = await td_list[3].text_content()
        self.payment_methods = [method.strip() for method in payment_method_list.split('\n')]

        # Создание и возврат объекта Offer
        return Offer(
            username=self.username,
            total_orders=self.total_orders,
            completion_rate=self.completion_rate,
            price=self.price,
            available_amount=self.available_amount,
            min_limit=self.min_limit,
            max_limit=self.max_limit,
            payment_methods=','.join(self.payment_methods) if self.payment_methods else '',
        )

    @staticmethod
    def parse_currency(input_string):
        match = re.match(r'([\d\s,]+)\s*([A-Z]+)', input_string)
        if match:
            number = match.group(1).replace('\xa0', '').replace(' ', '').replace(',', '.')
            currency = match.group(2)
            return float(number), currency
        return None, None


class Bybit:
    button_selector = 'div[role="dialog"].ant-modal button'
    price_selector = '.price-amount'

    def __init__(self, url: str, browser: str = 'webkit'):
        self.url = url
        self.browser = browser

    async def __call__(self) -> list[Offer]:
        async with async_playwright() as p:
            browser = await getattr(p, self.browser).launch()
            page = await browser.new_page()
            await page.goto(self.url)

            button = page.locator(self.button_selector)
            print(await button.count())
            try:
                await page.wait_for_selector(self.button_selector, timeout=2000)
            except playwright.async_api.TimeoutError:
                pass
            print(await button.count())
            if await button.is_visible():
                print("Кнопка найдена! Нажимаем...")
                await button.click()
            else:
                print("Кнопка не найдена.")

            offers = []
            for tr in await page.query_selector_all('tr'):
                offer = await OfferParser().parse(tr)
                if offer:
                    offers.append(offer)
            #await asyncio.sleep(50)
            await browser.close()
        return offers


class BybitService:
    def __init__(self, bybit_api: Bybit, service: OfficeRepositoryService, period_service: PeriodRepositoryService):
        self.bybit_api = bybit_api
        self.service = service
        self.period_service = period_service

    async def __call__(self) -> None:
        offers = await self.bybit_api()

        await self.period_service.create(
            await self.create_period(offers),
            auto_commit=True
        )

    async def create_period(self, offers: list[Offer]) -> PeriodEntity:
        prices = [offer.price for offer in offers]
        min_price = min(prices)
        max_price = max(prices)
        average = sum(prices) / len(prices) if prices else 0
        return PeriodEntity(
            min=min_price,
            max=max_price,
            average=average,
            offers=[
                await self.service.to_model(offer.__dict__)
                for offer in offers
            ]
        )

    @staticmethod
    def get_instance(session: AsyncSession) -> 'BybitService':
        return BybitService(
            bybit_api=Bybit(settings.bybit.url, settings.bybit.browser),
            service=OfficeRepositoryService(session=session),
            period_service=PeriodRepositoryService(session=session),
        )


if __name__ == "__main__":
    asyncio.run(Bybit("https://www.bybit.com/ru-RU/fiat/trade/otc/buy/USDT/RUB").__call__())