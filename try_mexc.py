# Using MEXC Subject

import asyncio
import datetime as dt
from abc import ABC, abstractmethod
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Dict
from loguru import logger

from mexc_toolkit import mexc_market

from config import TIMING, STABLE, RESPONSE_MAX_TIME


class Subject(ABC):
    @abstractmethod
    def register_observer(self, observer) -> None:
        pass

    @abstractmethod
    def remove_observer(self, observer) -> None:
        pass

    @abstractmethod
    def notify_users(self) -> None:
        pass


class Observer(ABC):
    @abstractmethod
    def price_updated(self, data) -> None:
        pass


class PriceListener(Subject):
    def __init__(self):
        self.__users: List[Observer] = []
        self.__data: Dict[str, float] = {}
        self.__mexc = mexc_market('https://api.mexc.com')
        self.__duration = TIMING['price_check']
        self.scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
        self.scheduler.start()

    def register_observer(self, observer) -> None:
        self.__users.append(observer)

    def remove_observer(self, observer) -> None:
        self.__users.remove(observer)

    def notify_users(self) -> None:
        for user in self.__users:
            user.price_updated(self.__data)

    def add_token(self, token, listing):
        logger.debug(f'Adding token {token} to Listener')
        symbol = token + STABLE
        self.scheduler.add_job(
            self.fetch_price,
            'date',
            run_date=listing,
            misfire_grace_time=5,
            kwargs={'symbol': symbol},
        )

    def remove_token(self, token):
        logger.debug(f'Removing token {token} from Listener')
        symbol = token + STABLE
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if token in job.kwargs['symbol']:
                self.scheduler.remove_job(job.id)
        del self.__data[symbol]

    def data_changed(self) -> None:
        self.notify_users()

    async def fetch_price(self, symbol) -> None:
        timelimit = dt.datetime.now() + dt.timedelta(seconds=self.__duration)
        while dt.datetime.now() <= timelimit:
            try:
                res = await asyncio.wait_for(
                    self.__mexc.get_price(params={'symbol': symbol}),
                    timeout=RESPONSE_MAX_TIME,
                )
                self.__data[symbol] = res['price']
                self.notify_users()
            except asyncio.TimeoutError:
                print('TIMEOUT while MEXC price waiting!')
            except Exception as e:
                print(f'Error: ')
            await asyncio.sleep(RESPONSE_MAX_TIME)


class User(Observer):
    def __init__(self, price_listener: PriceListener, balance):
        self.__listener = price_listener
        self.__listener.register_observer(self)
        self.balance: Dict[str, float] = balance

    def price_updated(self, data) -> None:
        logger.info(f'Prices has been updated. Data: {data}')
        for token, amount in self.balance.items():
            symbol = token + STABLE
            if symbol in data.keys():
                usdt_amount = amount * float(data[symbol])
                # logger.info(f"{token} balance is {usdt_amount}")


async def main():
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )

    price_listener = PriceListener()
    user1 = User(price_listener, {'ETH': 2, 'BTC': 1})
    logger.info(f'Добавили пользователя в роли наблюдателя')

    # btc_listing_time = dt.datetime(2024, 7, 15, 12, 2)
    btc_listing_time = dt.datetime.now() + dt.timedelta(seconds=1)
    eth_listing_time = btc_listing_time + dt.timedelta(seconds=10)

    price_listener.add_token('BTC', btc_listing_time)
    price_listener.add_token('ETH', eth_listing_time)

    loop_time = dt.datetime.now() + dt.timedelta(seconds=120)
    logger.info(f'Начинаем цикл на 2 минуты, чтобы шедулер отработал правильно')
    once = True
    while dt.datetime.now() <= loop_time:
        await asyncio.sleep(5)
        if once:
            price_listener.remove_token('BTC')
            once = False
    logger.success('Все замечательно')


if __name__ == '__main__':
    asyncio.run(main())
