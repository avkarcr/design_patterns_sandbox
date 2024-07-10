# Using MEXC Subject
import datetime
from abc import ABC, abstractmethod
import datetime as dt
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

    def __init__(self, timing, stable):
        self.__users: List[Observer] = []
        self.__data: Dict = {}
        self.stable = stable
        self.price_check = timing['price_check']

    def register_observer(self, observer) -> None:
        self.__users.append(observer)

    def remove_observer(self, observer) -> None:
        self.__users.remove(observer)

    def notify_users(self) -> None:
        for user in self.__users:
            user.update(self.__data)

    def add_token(self, token):
        self.__data[token + self.stable] = 0
        self.data_changed()

    def remove_token(self, token):
        del self.__data[token + self.stable]
        self.data_changed()

    def data_changed(self) -> None:
        self.notify_users()

    def get_token_price(self, token) -> float:
        timelimit = dt.datetime.now() + dt.timedelta(seconds=self.price_check)
        while dt.datetime.now() <= timelimit:
            try:
                res = self.__mexc.get_price(params={'symbol': token + self.stable})
                self.__data[token] = res['price']
                self.notify_users()
            except Exception as e:
                print(f'Error: ')
        return self.__data[token]


class User1(Observer):
    __listing: Listing
    __data: Dict

    def __init__(self, listing: Listing):
        self.__listing = listing
        listing.register_observer(self)

    def update(self, data) -> None:
        self.__data = data
        print(f'User_1 prices updated. Data: {data}')


class User2(Observer):
    __listing: Listing
    __data: Dict

    def __init__(self, listing: Listing):
        self.__listing = listing
        listing.register_observer(self)

    def update(self, data) -> None:
        self.__data = data
        print(f'User_2 prices updated. Data: {data}')


def main():
    timing = {}
    stable = 'USDT'
    timing['price_check'] = 500

    listing = Listing(
        timing=timing,
        stable=stable,
    )
    user1 = User1(listing)
    user2 = User2(listing)

    listing.add_token('MSI')
    listing.add_token('ATRK')

    listing.get_token_price('MSI')

    print('Well done!')


if __name__ == '__main__':
    main()
