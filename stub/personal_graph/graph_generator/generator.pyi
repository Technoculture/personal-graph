import abc
from abc import ABC, abstractmethod
from personal_graph.clients import OpenAILLMClient as OpenAILLMClient
from personal_graph.models import KnowledgeGraph as KnowledgeGraph

class TextToGraphParserInterface(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def generate(self, query: str) -> KnowledgeGraph: ...

class OpenAITextToGraphParser(TextToGraphParserInterface):
    system_prompt: str
    prompt: str
    llm_client: OpenAILLMClient
    def __init__(
        self, llm_client: OpenAILLMClient, system_prompt: str = ..., prompt: str = ...
    ) -> None: ...
    def generate(self, query: str) -> KnowledgeGraph: ...
