from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, signal, ts, ind):
        raise NotImplementedError


class Subject(ABC):
    @abstractmethod
    def register_observer(self, observer: Observer):
        raise NotImplementedError

    @abstractmethod
    def remove_observer(self, observer: Observer):
        raise NotImplementedError

    @abstractmethod
    def notify_observers(self):
        raise NotImplementedError


class Export(ABC):
    @abstractmethod
    def send(self):
        raise NotImplementedError
