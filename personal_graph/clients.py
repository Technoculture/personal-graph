import os
from abc import ABC, abstractmethod

import openai


class OpenAIClient(ABC):
    def __init__(self, client=None) -> None:
        if client is None:
            client = self._create_default_client()
        self.client = client

    @abstractmethod
    def _create_default_client(self):
        pass


class EmbeddingClient(OpenAIClient):
    def __init__(
        self, client=None, model_name="openai/text-embedding-3-small", dimensions=384
    ) -> None:
        super().__init__(client)
        self.model_name = model_name
        self.dimensions = dimensions

    def _create_default_client(self):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", ""),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        )


class LLMClient(OpenAIClient):
    def __init__(self, client=None, model_name="openai/gpt-3.5-turbo") -> None:
        super().__init__(client)
        self.model_name = model_name

    def _create_default_client(self):
        return openai.OpenAI(
            api_key="",
            base_url=os.getenv("LITE_LLM_BASE_URL", ""),
            default_headers={
                "Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN', '')}"
            },
        )
