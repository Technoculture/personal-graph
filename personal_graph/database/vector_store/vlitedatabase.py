import json
import uuid
from collections import deque
from typing import Dict, Any, List, Union, Callable, Optional, Set

from graphviz import Digraph  # type: ignore
from vlite import VLite  # type: ignore

from personal_graph.visualizers import _as_dot_node, _as_dot_label
from personal_graph.models import Node, Edge, KnowledgeGraph
from personal_graph.database.vector_store.new_vector_store import VectorStore


class VLiteDatabase(VectorStore):
    def __init__(
        self,
        *,
        collection: str = "collection",
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

    def add_node(self, label: str, attribute: Dict, id: Any):
        attribute.update({"label": label, "type": "node", "id": id})
        self.vlite.add(item_id=id, data={"text": label}, metadata=attribute)
        self.vlite.save()

    def add_nodes(
        self, attributes: List[Union[Dict[str, str]]], labels: List[str], ids: List[Any]
    ) -> None:
        for attribute, label, id in zip(attributes, labels, ids):
            self.add_node(label, attribute, id)

    def add_edge(self, source: Any, target: Any, label: str, attributes: Dict) -> None:
        edge_id = str(uuid.uuid4())
        attributes.update(
            {"source": source, "target": target, "label": label, "id": edge_id}
        )
        self.vlite.add({"text": label}, item_id=edge_id, metadata=attributes)
        self.vlite.save()

    def add_edges(
        self,
        sources: List[Any],
        targets: List[Any],
        labels: List[str],
        attributes: List[Union[Dict[str, str]]],
    ):
        for source, target, label, attribute in zip(
            sources, targets, labels, attributes
        ):
            self.add_edge(source, target, label, attribute)

    def update_node(self, node: Node):
        attributes = {"attribute": node.attributes}
        self.vlite.update(node.id, node.label, attributes)
        self.vlite.save()

    def remove_node(self, id: Any) -> None:
        self.vlite.delete(ids=[id])

    def remove_nodes(self, ids: List[Any]) -> None:
        self.vlite.delete(ids)

    def search_node(self, node_id: Any) -> Any:
        return self.vlite.get(ids=[node_id])

    def search_node_label(self, node_id: Any) -> Any:
        node_data = self.search_node([node_id])
        if node_data == []:
            return None

        return node_data[0][2]["label"]

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
        results = self.vlite.retrieve(text=json.dumps(data), top_k=limit)
        if results is None:
            return None

        if sort_by:
            results.sort(key=lambda x: x[2].get(sort_by, 0), reverse=descending)

        if threshold is not None:
            return [res for res in results if res[3] < threshold][:limit]

        return results[:limit]

    def fetch_ids_from_db(self) -> List[str]:
        ids = []
        collection = self.vlite.dump()
        for key, _ in collection.items():
            id_without_suffix = key.split("_")[0]
            ids.append(id_without_suffix)
        return ids

    def search_indegree_edges(self, target: Any) -> List[Any]:
        return self.vlite.get(where={"target": target})

    def search_outdegree_edges(self, source: Any) -> List[Any]:
        return self.vlite.get(where={"source": source})

    def _connections_in(self, identifier: Any) -> List[Any]:
        return self.vlite.get(where={"target": identifier})

    def _connections_out(self, identifier: Any) -> List[Any]:
        return self.vlite.get(where={"source": identifier})

    def get_connections(
        self, identifier: Any, direction: Optional[Callable[[Any], List[Any]]] = None
    ) -> List[Any]:
        if direction is None:
            return self._connections_in(identifier) + self._connections_out(identifier)
        else:
            return direction(identifier)

    def all_connected_nodes(self, node_or_edge: Union[Node, Edge]):
        connected_nodes: Set[str | int] = set()
        if isinstance(node_or_edge, Node):
            connected_nodes.update(
                item["source"] for item in self.search_outdegree_edges(node_or_edge.id)
            )
            connected_nodes.update(
                item["target"] for item in self.search_indegree_edges(node_or_edge.id)
            )
        elif isinstance(node_or_edge, Edge):
            connected_nodes.add(node_or_edge.source)
            connected_nodes.add(node_or_edge.target)
        return [self.search_node(node_id) for node_id in connected_nodes]

    def graphviz_visualize(
        self,
        dot_file: Optional[str] = None,
        path: List[Any] = [],
        connections: Any = None,
        format: str = "png",
        exclude_node_keys: List[str] = [],
        hide_node_key: bool = False,
        node_kv: str = " ",
        exclude_edge_keys: List[str] = [],
        hide_edge_key: bool = False,
        edge_kv: str = " ",
    ) -> Digraph:
        if connections is None:
            connections = self.get_connections
        ids = []
        for i in path:
            ids.append(str(i))
            for edge in connections(i):  # type: ignore
                src = edge[2]["source"]
                tgt = edge[2]["target"]
                if src not in ids:
                    ids.append(src)
                if tgt not in ids:
                    ids.append(tgt)

        dot = Digraph()

        visited = []
        edges = []
        for i in ids:
            if i not in visited:
                node = self.search_node(i)  # type: ignore

                if node == []:
                    continue

                name, label = _as_dot_node(
                    node[0][2], exclude_node_keys, hide_node_key, node_kv
                )
                dot.node(name, label=label)
                for edge in connections(i):  # type: ignore
                    if edge not in edges:
                        src, tgt, props = edge
                        dot.edge(
                            str(src),
                            str(tgt),
                            label=_as_dot_label(
                                props, exclude_edge_keys, hide_edge_key, edge_kv
                            )
                            if props
                            else None,
                        )
                        edges.append(edge)
                visited.append(i)

        dot.render(dot_file, format=format)
        return dot

    def search_from_graph(
        self, text: str, *, limit: int = 5, descending: bool = False, sort_by: str = ""
    ) -> KnowledgeGraph:
        try:
            similar_nodes = self.vector_search_node(
                {"body": text}, descending=descending, limit=limit, sort_by=sort_by
            )

            similar_edges = self.vector_search_edge(
                {"body": text}, descending=descending, limit=limit, sort_by=sort_by
            )

            resultant_subgraph = KnowledgeGraph()

            if similar_edges and similar_nodes is None or similar_nodes is None:
                return resultant_subgraph

            for node in similar_nodes:
                similar_node = Node(
                    id=node[0],
                    label=node[1],
                    attributes=(node[2])["body"],
                )
                resultant_subgraph.nodes.append(similar_node)

                nodes = self.all_connected_nodes(similar_node)

                if not nodes:
                    continue

                for i in nodes:
                    if i not in resultant_subgraph.nodes:
                        node = Node(
                            id=i[0][0],
                            label=i[0][1],
                            attributes=(i[0][2])["body"],
                        )
                        resultant_subgraph.nodes.append(node)

            for edge in similar_edges:
                edge = self.search_node(edge[0].rstrip("_0"))

                if edge == []:
                    continue

                if "source" not in edge[0][2].keys():
                    continue

                else:
                    similar_edge = Edge(
                        source=edge[0][2]["source"],
                        target=edge[0][2]["target"],
                        label=edge[0][1],
                        attributes=edge[0][2]["body"],
                    )
                    resultant_subgraph.edges.append(similar_edge)

                    nodes = self.all_connected_nodes(similar_edge)
                    if not nodes:
                        continue

                    for i in nodes:
                        if i not in resultant_subgraph.nodes:
                            node = Node(
                                id=i[0][0],
                                label=i[0][1],
                                attributes=(i[0][2])["body"],
                            )
                            resultant_subgraph.nodes.append(node)

        except KeyError:
            return KnowledgeGraph()

        return resultant_subgraph

    def search(
        self,
        text: str,
        *,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ):
        try:
            similar_nodes = self.vector_search_node(
                {"body": text},
                threshold=4500,
                descending=descending,
                limit=limit,
                sort_by=sort_by,
            )

        except KeyError:
            return []

        if similar_nodes is None:
            return None

        if limit == 1:
            return similar_nodes[0][2]

        return similar_nodes

    def find_nodes_like(self, label: str, threshold: float) -> List[Node]:
        nodes = self.vlite.get(where={"label": label})

        similar_nodes = []
        for node in nodes:
            node_id, node_text, node_metadata = node
            retrieved_nodes = self.vlite.retrieve(
                text=node_text, top_k=5, return_scores=True
            )

            if not retrieved_nodes:
                continue

            for similar_node in retrieved_nodes:
                if (
                    similar_node
                    and similar_node not in similar_nodes
                    and similar_node[3] <= threshold
                ):
                    node = Node(
                        id=similar_node[2]["id"],
                        label=similar_node[1],
                        attributes=similar_node[2],
                    )
                    similar_nodes.append(node)

        return similar_nodes

    def merge_by_similarity(self, threshold) -> None:
        nodes = self.vlite.get(where={"type": "node"})

        for node_id in nodes:
            node_data = self.search_node(node_id[0])

            if not node_data:
                continue

            node = Node(
                id=node_data[0][0],
                label=node_data[0][1],
                attributes=json.dumps(node_data[0][2]),
            )

            similar_nodes = self.vlite.retrieve(
                text=json.dumps(node_data[0][2]), top_k=3, return_scores=True
            )

            if not similar_nodes:
                continue

            for similar_node in similar_nodes:
                if similar_node[3] >= threshold:
                    continue

                similar_node_id = similar_node[0]

                if similar_node_id == node_id:
                    continue

                in_degree_edges = self.search_indegree_edges(similar_node_id)

                out_degree_edges = self.search_outdegree_edges(similar_node_id)

                concatenated_attributes = json.loads(node.attributes).copy()  # type: ignore
                concatenated_labels = node.label

                for edge in in_degree_edges:
                    for key, value in edge[2].items():
                        if key in concatenated_attributes:
                            concatenated_attributes[key] += value
                        else:
                            concatenated_attributes[key] = value

                    concatenated_labels += "," + edge[1]

                for edge in out_degree_edges:
                    self.add_edge(similar_node_id, edge[2]["target"], edge[1], edge[2])

                    for key, value in edge[2].items():
                        if key in concatenated_attributes:
                            concatenated_attributes[key] += value
                        else:
                            concatenated_attributes[key] = value

                    concatenated_labels += "," + edge[1]

                self.update_node(
                    Node(
                        id=node.id,
                        label=concatenated_labels,
                        attributes=json.dumps(concatenated_attributes),
                    )
                )
                self.remove_node(similar_node_id)

        self.vlite.save()

    def traverse(
        self, source: Any, target: Optional[Any] = None, with_bodies: bool = False
    ) -> List:
        if source is None:
            return []

        visited = set()
        queue: deque = deque([(source, [])])
        paths = []

        while queue:
            node, path = queue.popleft()
            visited.add(node)
            path = path + [node]

            if target is None or node == target:
                if with_bodies:
                    node_data = self.search_node(node)
                    if node_data:
                        node_path = [
                            (node_id, node_label, node_attributes)
                            for node_id, node_label, node_attributes in node_data
                        ]
                        if node_path not in paths:
                            paths.append(node_path)
                else:
                    if path not in paths:
                        paths.append(path)

            connections = self.get_connections(node, self._connections_out)

            for conn in connections:
                neighbor = conn[2]["target"]
                if neighbor not in visited:
                    queue.append((neighbor, path))

        return paths
