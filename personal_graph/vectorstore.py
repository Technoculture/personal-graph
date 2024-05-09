"""
Provide access to different vector databases
"""

from abc import ABC, abstractmethod


class VectorStore(ABC):
    @abstractmethod
    def get(self) -> list[float]:
        pass


class SqliteVss(VectorStore):
    def __init__(self) -> None:
        pass

    def get(self) -> list[float]:
        pass


class Vlite2(VectorStore):
    def __init__(self) -> None:
        pass

    def get(self) -> list[float]:
        pass
