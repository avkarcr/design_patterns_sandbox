# Using MEXC Subject

import asyncio
import datetime as dt
from abc import ABC, abstractmethod
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import List, Dict

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
    __users: List[Observer]
    __data: Dict
    __mexc = mexc_market('https://api.mexc.com')

    def __init__(self, timing):
        self.__users: List[Observer] = []
        self.__data: Dict = {}
        self.price_check = timing['price_check']
        self.scheduler = AsyncIOScheduler({'apscheduler.timezone': 'Europe/Moscow'})
        self.scheduler.start()
        self._running_state: bool = True

    def register_observer(self, observer) -> None:
        self.__users.append(observer)

    def remove_observer(self, observer) -> None:
        self.__users.remove(observer)

    def notify_users(self) -> None:
        for user in self.__users:
            user.update(self.__data)

    def add_token(self, token):
        self.__data[token + 'USDT'] = 0
        # self.scheduler.add_job(
        #     self.fetch_price,
        #     'date',
        #     run_date=dt.datetime.now() + dt.timedelta(seconds=1),
        #     misfire_grace_time=5,
        #     kwargs={'token': token},
        # )
        self.data_changed()

    def remove_token(self, token):
        del self.__data[token + 'USDT']
        self.data_changed()

    def data_changed(self) -> None:
        self.notify_users()

    async def fetch_price(self, token) -> None:
        self._running_state = True
        timelimit = dt.datetime.now() + dt.timedelta(seconds=self.price_check)
        while dt.datetime.now() <= timelimit or self._running_state:
            print("Время:", dt.datetime.now().strftime("%H:%M:%S"))
            try:
                res = await asyncio.wait_for(
                    self.__mexc.get_price(params={'symbol': token + 'USDT'}),
                    timeout=2,
                )
                self.__data[token] = res['price']
                self.notify_users()
            except asyncio.TimeoutError:
                print('TIMEOUT while MEXC price waiting!')
            except Exception as e:
                print(f'Error: ')
            await asyncio.sleep(0.5)


class User1(Observer):
    __listing: Listing
    __data: Dict

    def __init__(self, listing: Listing, token):
        self.__listing = listing
        listing.register_observer(self)
        listing.add_token(token)

    # def add_token(self, token, listing_time) -> None:
    #     self.__data = data
    #     print(f'User_1 prices updated. Data: {data}')

    def update(self, data) -> None:
        self.__data = data
        print(f'User_1 prices updated. Data: {data}')


def main():
    timing = {
        'price_check': 30,
    }

    listing = Listing(
        timing=timing,
    )

    user1 = User1(listing, 'MSI')

    # listing.add_token('MSI')
    # listing.add_token('ATRK')

    print('Well done!')


if __name__ == '__main__':
    main()
