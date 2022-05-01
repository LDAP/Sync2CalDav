
from abc import abstractmethod
from typing import Protocol
from caldav.objects import Calendar


class ToDoSynchronizer(Protocol):
    @abstractmethod
    def __init__(self):
        ...

    @abstractmethod
    async def sync_todos(self, calendar: Calendar):
        ...
