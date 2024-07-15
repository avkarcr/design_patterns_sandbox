# Simple Example
from loguru import logger
import asyncio
import datetime as dt
from abc import ABC, abstractmethod
from typing import List, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from mexc_toolkit import mexc_market


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
    def update(self, data) -> None:
        pass


class Listing(Subject):
    def __init__(self):
        self.__users: List[Observer] = []
        self.__data: Dict[str, float] = {}
        self.__mexc = mexc_market('https://api.mexc.com')
        self.running_state = True

    def register_observer(self, observer) -> None:
        self.__users.append(observer)

    def remove_observer(self, observer) -> None:
        self.__users.remove(observer)

    def notify_users(self) -> None:
        for user in self.__users:
            user.update(self.__data)

    def data_changed(self) -> None:
        self.notify_users()

    async def fetch_price(self, symbol: str) -> None:
        duration = 5
        feedback_time = 0.5
        print(dt.datetime.now().strftime("%H:%M:%S"), f'START running FETCH_PRICE for {symbol} for {duration} sec.')
        timelimit = dt.datetime.now() + dt.timedelta(seconds=duration)
        while dt.datetime.now() <= timelimit:
            try:
                res = await asyncio.wait_for(
                    self.__mexc.get_price(params={'symbol': symbol}),
                    timeout=feedback_time,
                )
                self.__data[symbol] = float(res['price'])
                self.data_changed()
            except asyncio.TimeoutError:
                print(dt.datetime.now().strftime("%H:%M:%S"), 'TIMEOUT while MEXC price waiting!')
            except Exception as e:
                print(dt.datetime.now().strftime("%H:%M:%S"), f'Error: {e}')
            await asyncio.sleep(feedback_time)
        del self.__data[symbol]
        print(dt.datetime.now().strftime("%H:%M:%S"), f'STOP running FETCH_PRICE for {symbol}')


class User(Observer):
    def __init__(self, listing: Listing):
        self.__listing = listing
        self.__listing.register_observer(self)
        self.__data: Dict[str, float] = {}

    def update(self, data) -> None:
        self.__data = data
        print(f'Data updated: {data}')


async def main():
    logger.remove()  # Удаляем стандартный обработчик
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level><u>{level: <8}</u></level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )

    listing = Listing()
    user1 = User(listing)

    scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
    scheduler.start()
    scheduler.add_job(
        listing.fetch_price,
        'date',
        run_date=dt.datetime.now() + dt.timedelta(seconds=1),
        misfire_grace_time=5,
        kwargs={'symbol': 'BTCUSDT'}
    )
    scheduler.add_job(
        listing.fetch_price,
        'date',
        run_date=dt.datetime.now() + dt.timedelta(seconds=5),
        misfire_grace_time=5,
        kwargs={'symbol': 'ETHUSDT'}
    )
    scheduler.add_job(
        listing.fetch_price,
        'date',
        run_date=dt.datetime.now() + dt.timedelta(seconds=10),
        misfire_grace_time=5,
        kwargs={'symbol': 'MXUSDT'}
    )

    while True:
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
