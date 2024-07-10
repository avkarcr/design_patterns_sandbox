# Observer Design Pattern

from abc import ABC, abstractmethod
from typing import List

'''
У нас есть класс WeatherData, который от физических датчиков регулярно получает
значения по трем показателям:
1. Температура
2. Влажность
3. Давление

ЛОГИКА паттерна:
Субъект - класс WeaterData
Наблюдатели - гаджеты
Субъект всегда имеет последние данные.
Наблюдатели (гаджеты) получают последние данные от субъекта.

'''


class Subject(ABC):
    '''
    Реализует интерфейс субъекта - делает обязательными для
    всех подклассов три следующие метода для работы с наблюдателями:
    register_observer - для регистрации наблюдателя в подписчиках
    remove_observer - для удаления наблюдателя из подписчиков
    notify_observers - для оповещения всех зарегистрированных наблюдателей
    '''
    @abstractmethod
    def register_observer(self, observer) -> None:
        pass

    @abstractmethod
    def remove_observer(self, observer) -> None:
        pass

    @abstractmethod
    def notify_observers(self) -> None:
        pass


class Observer(ABC):
    '''
    Реализует интерфейс наблюдателя - делает обязательным для
    всех подклассов метод для обновления данных:
    update
    '''
    @abstractmethod
    def update(self, temperature, humidity, pressure) -> None:
        pass


class WeatherData(Subject):
    __observers: List[Observer]
    __temperature: float
    __humidity: float
    __pressure: float

    def __init__(self):
        self.__observers: List[Observer] = []

    def register_observer(self, observer) -> None:
        self.__observers.append(observer)

    def remove_observer(self, observer) -> None:
        self.__observers.remove(observer)

    def notify_observers(self) -> None:
        for observer in self.__observers:
            observer.update(
                temperature=self.__temperature,
                humidity=self.__humidity,
                pressure=self.__pressure,
            )

    def measurements_changed(self) -> None:
        self.notify_observers()

    def set_measurements(self, temperature, humidity, pressure) -> None:
        self.__temperature = temperature
        self.__humidity = humidity
        self.__pressure = pressure
        self.measurements_changed()

    def get_temperature(self) -> float:
        return self.__temperature

    def get_humidity(self) -> float:
        return self.__humidity

    def get_pressure(self) -> float:
        return self.__pressure


class Widget1(Observer):
    __weather_data: WeatherData
    __temperature: float
    __humidity: float
    __pressure: float

    def __init__(self, weather_data: WeatherData):
        self.__weather_data = weather_data
        weather_data.register_observer(self)

    def update(self, temperature, humidity, pressure) -> None:
        self.__temperature = temperature
        self.__humidity = humidity
        self.__pressure = pressure
        print('Widget_1 measures updated')


class Widget2(Observer):
    __weather_data: WeatherData
    __temperature: float

    def __init__(self, weather_data: WeatherData):
        self.__weather_data = weather_data
        weather_data.register_observer(self)

    def update(self, temperature, humidity, pressure) -> None:
        self.__temperature = temperature
        print('Widget_2 measure updated (temperature)')


def main():
    weather_data = WeatherData()
    widget1 = Widget1(weather_data)
    widget2 = Widget2(weather_data)

    weather_data.set_measurements(28, 70, 30)
    weather_data.set_measurements(30, 81, 27)
    weather_data.remove_observer(widget2)
    weather_data.set_measurements(24, 66, 33)

    print('Well done!')


if __name__ == '__main__':
    main()
