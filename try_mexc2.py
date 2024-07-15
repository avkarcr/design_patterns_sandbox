# Simple Example

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
        self.__symbols: List[str] = []
        self.__mexc = mexc_market('https://api.mexc.com')
        self.__queue = asyncio.Queue()
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

    async def add_symbol(self, symbol: str):
        await self.__queue.put(('add', symbol))

    async def remove_symbol(self, symbol: str):
        await self.__queue.put(('remove', symbol))

    async def manage_symbols(self):
        while self.running_state:
            action, symbol = await self.__queue.get()
            if action == 'add':
                if symbol not in self.__symbols:
                    self.__symbols.append(symbol)
                    print(f'Добавили символ {symbol}')
            elif action == 'remove':
                if symbol in self.__symbols:
                    self.__symbols.remove(symbol)
                    print(f'Удалили символ {symbol}')
            self.__queue.task_done()

    async def start_fetching(self):
        while self.running_state:
            print(f'НАЧАЛО ЦИКЛА. Список символов: {self.__symbols}')
            if not self.__symbols:
                print('Список символов пустой, ничего не делаем 1 секунду...')
                await asyncio.sleep(1)
                continue
            tasks = [self.fetch_price(symbol) for symbol in self.__symbols]
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)
            print('КОНЕЦ ЦИКЛА')

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

    while True:
        print('Unlimited loop - start')
        await asyncio.sleep(5)
        print('Unlimited loop - continue')

if __name__ == '__main__':
    asyncio.run(main())
