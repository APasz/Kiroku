"""For storing data"""
from dataclasses import dataclass

from logging import Logger

print(__name__)


class Singleton(type):
    """Singleton for singles, singlings, singlers, singletones, singlators, singlatees, and singlated..."""

    _instances = {}

    def __call__(cls, *args, **kwargs):  # noqa: D102
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass(slots=True)
class Store(metaclass=Singleton):
    """For storing data"""

    logs: dict[int, Logger]
    indev: bool
    extensions_dict: dict


# MIT APasz
