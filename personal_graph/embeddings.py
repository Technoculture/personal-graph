"""
Provide access to different embeddings models
"""

from abc import ABC, abstractmethod

import ollama  # type: ignore
import openai


class EmbeddingsModel(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> list[float]:
        pass


class OpenAIEmbeddingsModel(EmbeddingsModel):
    def __init__(
        self, embed_client: openai.OpenAI, embed_model: str, embed_dimension: int = 384
    ) -> None:
        self.client = embed_client if embed_client else None
        self.model = embed_model
        self.dimension = embed_dimension

    def __repr__(self) -> str:
        return (
            f"OpenAIEmbeddingsModel(\n"
            f"    embed_client={self.client},\n"
            f"    embed_model='{self.model}',\n"
            f"    embed_dimension={self.dimension}\n"
            f"  )"
        )

    def get_embedding(self, text: str) -> list[float]:
        if self.client is None:
            return []
        text = text.replace("\n", " ")
        return (
            self.client.embeddings.create(
                input=[text],
                model=self.model,
                dimensions=self.dimension,
                encoding_format="float",
            )
            .data[0]
            .embedding
        )


class OllamaEmbeddingModel(EmbeddingsModel):
    def __init__(
        self, embed_client: ollama.Client, embed_model: str, embed_dimension: int = 768
    ) -> None:
        self.client = embed_client if embed_client else None
        self.model = embed_model
        self.dimension = embed_dimension

    def __repr__(self) -> str:
        return (
            f"OllamaEmbeddingModel(\n"
            f"    embed_client={self.client},\n"
            f"    embed_model='{self.model}',\n"
            f"    embed_dimension={self.dimension}\n"
            f"  )"
        )

    def get_embedding(self, text: str) -> list[float]:
        if self.client is None:
            return []

        return ollama.embeddings(
            model=self.model,
            prompt=text,
        )["embedding"]
