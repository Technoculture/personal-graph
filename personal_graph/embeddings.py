"""
Provide access to different embeddings models
"""

import os
from abc import ABC, abstractmethod
from openai import OpenAI  # type: ignore


class EmbeddingsModel(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        pass


class OpenAIEmbeddingsModel(EmbeddingsModel):
    def __init__(self) -> None:
        base_url = os.getenv("LITE_LLM_BASE_URL")
        headers = {"Authorization": f"Bearer {os.getenv('LITE_LLM_TOKEN')}"}
        self.client = (
            OpenAI(api_key="", base_url=base_url, default_headers=headers)
            if base_url and headers
            else None
        )
        self.model = "embeddings"

    def get_embedding(self, text: str) -> list[float]:
        if self.client is None:
            return []
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(
                input=[text], model=self.model, dimensions=384, encoding_format="float"
            )
            .data[0]
            .embedding
        )
