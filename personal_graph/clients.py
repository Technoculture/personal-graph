import os
import openai

from abc import ABC, abstractmethod


class APIClient(ABC):
    # def __init__(self, client=None) -> None:
    #     if client is None:
    #         client = self._create_default_client()
    #     self.client = client

    @abstractmethod
    def _create_default_client(self):
        pass


class EmbeddingModel(ABC):
    # def __init__(self, client=None) -> None:
    #     if client is None:
    #         client = self._create_default_client()
    #     self.client = client

    @abstractmethod
    def _create_default_client(self):
        pass


@dataclasses
class OpenAIEmbeddingModel(EmbeddingModel):
    model_name: str = "text-embedding-3-small"
    dimensions: Optional[int] = 384
    api_key: str = ""

    def __post_init__(self):
        return openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", self.api_key)
        )

@dataclasses
class LiteLLMEmbeddingClient(APIClient):
    model_name: str = "text-embedding-3-small"
    dimensions: Optional[int] = 384
    base_url: str = ""

    def _create_default_client(self):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", self.base_url),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        )

@dataclasses
class OllamaEmbeddingClient(APIClient):
    model_name: str = "text-embedding-3-small"
    dimensions: Optional[int]
    # def __init__(
    #     self, client=None, model_name="openai/text-embedding-3-small", dimensions=384
    # ) -> None:
    #     super().__init__(client)
    #     self.model_name = model_name
    #     self.dimensions = dimensions

    def _create_default_client(self):
        return ollama.Ollama()


class OpenAILLMClient(APIClient):
    def __init__(self, client=None, model_name="openai/gpt-3.5-turbo") -> None:
        # super().__init__(client)
        self.model_name = model_name

    def _create_default_client(self):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", ""),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        )
