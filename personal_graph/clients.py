import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from dotenv import load_dotenv
from personal_graph.embeddings import OpenAIEmbeddingsModel, OllamaEmbeddingModel

import openai
import ollama  # type: ignore

load_dotenv()


class APIClient(ABC):
    @abstractmethod
    def _create_default_client(self, *args, **kwargs):
        pass


class EmbeddingClient(ABC):
    @abstractmethod
    def _create_default_client(self):
        pass

    @abstractmethod
    def get_embedding_model(self):
        pass


@dataclass
class OpenAIEmbeddingClient(EmbeddingClient):
    dimensions: int = 384
    model_name: str = "text-embedding-3-small"
    api_key: str = ""

    def __post_init__(self, *args, **kwargs):
        self.client = self._create_default_client(*args, **kwargs)

    def _create_default_client(self, *args, **kwargs):
        return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", self.api_key), *args, **kwargs)

    def get_embedding_model(self):
        return OpenAIEmbeddingsModel(self.client, self.model_name, self.dimensions)


@dataclass
class LiteLLMEmbeddingClient(APIClient):
    model_name: str = "openai/text-embedding-3-small"
    dimensions: int = 384
    base_url: str = ""

    def __post_init__(self, *args, **kwargs):
        self.client = self._create_default_client(*args, **kwargs)

    def _create_default_client(self, *args, **kwargs):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", self.base_url),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
            *args,
            **kwargs,
        )

    def get_embedding_model(self):
        return OpenAIEmbeddingsModel(self.client, self.model_name, self.dimensions)


@dataclass
class OllamaEmbeddingClient(APIClient):
    model_name: str
    dimensions: int = 768

    def __post_init__(self, *args, **kwargs):
        self.client = self._create_default_client(*args, **kwargs)

    def _create_default_client(self, *args, **kwargs):
        return ollama.Client(*args, **kwargs)

    def get_embedding_model(self):
        return OllamaEmbeddingModel(self.client, self.model_name, self.dimensions)


@dataclass
class LiteLLMClient(APIClient):
    base_url: str = ""
    model_name: str = "openai/gpt-3.5-turbo"

    def __post_init__(self, *args, **kwargs):
        self.client = self._create_default_client(*args, **kwargs)

    def _create_default_client(self, *args, **kwargs):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", self.base_url),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
            *args,
            **kwargs,
        )


@dataclass
class OpenAIClient(APIClient):
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = "gpt-3.5-turbo"

    def __post_init__(self, *args, **kwargs):
        self.client = self._create_default_client(*args, **kwargs)

    def _create_default_client(self, *args, **kwargs):
        return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""), *args, **kwargs)


@dataclass
class OllamaClient(APIClient):
    model_name: str
    base_url: str = "http://localhost:11434/v1"
    api_key: str = "ollama"

    def __post_init__(self, *args, **kwargs):
        self.client = self._create_default_client(*args, **kwargs)

    def _create_default_client(self, *args, **kwargs):
        return ollama.Client(*args, **kwargs)
