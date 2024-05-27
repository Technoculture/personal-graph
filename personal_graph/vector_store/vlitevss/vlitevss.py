import json
from typing import Dict, Optional, Any, List, Union

from vlite import VLite  # type: ignore

from personal_graph.vector_store.vector_store import VectorStore


class VliteVSS(VectorStore):
    def __init__(
        self,
        *,
        collection: str = "./vectors",
        model_name: str = "mixedbread-ai/mxbai-embed-large-v1",
    ):
        self.collection = collection
        self.model_name = model_name

    def initialize(self):
        self.vlite = VLite(collection=self.collection, model_name=self.model_name)
        return self.vlite

    def __eq__(self, other):
        return self.collection == other.collection

    def save(self):
        self.vlite.save()

    def add_node_embedding(self, id: Any, label: str, attribute: Dict):
        count = self.vlite.count() + 1
        attribute.update({"label": label, "embed_id": count})
        self.vlite.add(
            item_id=id,
            data={"text": json.dumps(attribute)},
            metadata={"embed_id": count},
        )
        self.vlite.save()

    def add_edge_embedding(
        self, source: Any, target: Any, label: str, attributes: Dict
    ) -> None:
        count = self.vlite.count() + 1
        attributes.update(
            {"source": source, "target": target, "label": label, "embed_id": count}
        )
        self.vlite.add({"text": json.dumps(attributes)}, metadata={"embed_id": count})
        self.vlite.save()

    def add_edge_embeddings(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Union[Dict[str, str]]],
    ):
        for i, x in enumerate(zip(sources, targets, labels, attributes)):
            self.add_edge_embedding(x[0], x[1], x[2], x[3])

    def delete_node_embedding(self, ids: Any) -> None:
        for id in ids:
            id_to_be_deleted = self.vlite.get(where={"embed_id": id})
            self.vlite.delete(id_to_be_deleted)

    def delete_edge_embedding(self, ids: Any) -> None:
        id_to_be_deleted = self.vlite.get(where={"embed_id": id})
        self.vlite.delete(id_to_be_deleted)

    def vector_search_node(
        self,
        data: Dict,
        *,
        threshold: Optional[float] = None,
        descending: bool,
        limit: int,
        sort_by: str,
    ):
        results = self.vlite.retrieve(
            text=json.dumps(data), top_k=limit, return_scores=True
        )

        if results is None:
            return None

        if sort_by:
            results.sort(key=lambda x: x[2].get(sort_by, 0), reverse=descending)

        if threshold is not None:
            return [res for res in results if res[3] < threshold][:limit]

        return results[:limit]

    def vector_search_edge(
        self,
        data: Dict,
        *,
        threshold: Optional[float] = None,
        descending: bool,
        limit: int,
        sort_by: str,
    ):
        results = self.vlite.retrieve(
            text=json.dumps(data), top_k=limit, return_scores=True
        )
        if results is None:
            return None

        if sort_by:
            results.sort(key=lambda x: x[2].get(sort_by, 0), reverse=descending)

        if threshold is not None:
            return [res for res in results if res[3] < threshold][:limit]

        return results[:limit]

    def vector_search_node_from_multi_db(
        self, data: Dict, *, threshold: Optional[float] = None, limit: int = 1
    ):
        results = self.vlite.retrieve(
            text=json.dumps(data), top_k=limit, return_scores=True
        )

        if results is None:
            return None

        if threshold is not None:
            return [res for res in results if res[3] < threshold][:limit]

        return results[:limit]

    def vector_search_edge_from_multi_db(
        self, data: Dict, *, threshold: Optional[float] = None, limit: int = 1
    ):
        results = self.vlite.retrieve(
            text=json.dumps(data), top_k=limit, return_scores=True
        )

        if results is None:
            return None

        if threshold is not None:
            return [res for res in results if res[3] < threshold][:limit]

        return results[:limit]
