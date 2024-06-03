import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
import openai


class APIClient(ABC):
    @abstractmethod
    def _create_default_client(self):
        pass


# class EmbeddingModel(ABC):
#     @abstractmethod
#     def _create_default_client(self):
#         pass


# @dataclass
# class OpenAIEmbeddingModel(EmbeddingModel):
#     model_name: str = "text-embedding-3-small"
#     dimensions: Optional[int] = 384
#     api_key: str = ""
#
#     def __post_init__(self):
#         self.client = self._create_default_client()
#
#     def _create_default_client(self):
#         return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", self.api_key))


@dataclass
class LiteLLMEmbeddingClient(APIClient):
    model_name: str = "openai/text-embedding-3-small"
    dimensions: int = 384
    base_url: str = ""

    def __post_init__(self):
        self.client = self._create_default_client()

    def _create_default_client(self):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", self.base_url),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        )


# @dataclass
# class OllamaEmbeddingClient(APIClient):
#     model_name: str = "text-embedding-3-small"
#     dimensions: Optional[int]
#
#     def _create_default_client(self):
#         return ollama.Ollama()


@dataclass
class LiteLLMClient(APIClient):
    base_url: str = ""
    model_name: str = "openai/gpt-3.5-turbo"

    def __post_init__(self):
        self.client = self._create_default_client()

    def _create_default_client(self):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", self.base_url),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        )


@dataclass
class OpenAIClient(APIClient):
    api_key: str = os.getenv("OPEN_AI_KEY", "")
    model_name: str = "gpt-3.5-turbo"

    def __post_init__(self):
        self.client = self._create_default_client()

    def _create_default_client(self):
        return openai.OpenAI(api_key=os.getenv("OPEN_API_KEY", self.api_key))
