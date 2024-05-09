import os
from abc import ABC, abstractmethod
from typing import Optional

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


class DBClient:
    def __init__(
        self,
        db_url: Optional[str] = None,
        db_auth_token: Optional[str] = None,
        use_in_memory: Optional[bool] = False,
        vector0_so_path: Optional[str] = None,
        vss0_so_path: Optional[str] = None,
    ):
        self.db_url = db_url
        self.db_auth_token = db_auth_token
        self.use_in_memory = use_in_memory
        self.vector0_so_path = vector0_so_path
        self.vss0_so_path = vss0_so_path
