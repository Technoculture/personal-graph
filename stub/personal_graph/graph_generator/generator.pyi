import abc
from abc import ABC, abstractmethod
from typing import Union

from personal_graph.clients import OpenAIClient, LiteLLMClient
from personal_graph.models import KnowledgeGraph as KnowledgeGraph

class TextToGraphParserInterface(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def generate(self, query: str) -> KnowledgeGraph: ...

class OpenAITextToGraphParser(TextToGraphParserInterface):
    system_prompt: str
    prompt: str
    llm_client: Union[OpenAIClient, LiteLLMClient]
    def __init__(
        self, llm_client: OpenAIClient, system_prompt: str = ..., prompt: str = ...
    ) -> None: ...
    def generate(self, query: str) -> KnowledgeGraph: ...
