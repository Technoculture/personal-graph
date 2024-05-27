import abc
import openai
from _typeshed import Incomplete
from abc import ABC, abstractmethod

class EmbeddingsModel(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def get_embedding(self, text: str) -> list[float]: ...

class OpenAIEmbeddingsModel(EmbeddingsModel):
    client: Incomplete
    model: Incomplete
    dimension: Incomplete
    def __init__(
        self, embed_client: openai.OpenAI, embed_model: str, embed_dimension: int
    ) -> None: ...
    def get_embedding(self, text: str) -> list[float]: ...
