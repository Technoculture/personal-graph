from __future__ import annotations

import json
import logging
import uuid
from typing import Any, List, Optional, Union, Dict, Tuple

from contextlib import AbstractContextManager

from graphviz import Digraph  # type: ignore
from dotenv import load_dotenv
from owlready2 import Ontology  # type: ignore

from personal_graph import OpenAIClient
from personal_graph.database import TursoDB, SQLite
from personal_graph.graph_generator import (
    OpenAITextToGraphParser,
    OllamaTextToGraphParser,
)
from personal_graph.helper import validate_fhir_resource
from personal_graph.models import Node, EdgeInput, KnowledgeGraph, Edge
from personal_graph.vector_store import SQLiteVSS, VliteVSS

try:
    import fhir.resources as fhir  # type: ignore
except ImportError:
    logging.info("fhir module is not available.")

load_dotenv()


class GraphDB(AbstractContextManager):
    def __init__(
        self,
        *,
        vector_store: Union[SQLiteVSS, VliteVSS] = VliteVSS(collection="./vectors"),
        database: Union[TursoDB, SQLite] = SQLite(use_in_memory=True),
        graph_generator: Union[
            OpenAITextToGraphParser, OllamaTextToGraphParser
        ] = OpenAITextToGraphParser(llm_client=OpenAIClient()),
        ontologies: Optional[List[Union[Ontology, Any]]] = None,
    ):
        self.vector_store = vector_store
        self.db = database
        self.graph_generator = graph_generator
        self.db.initialize()
        self.vector_store.initialize()
        self.ontologies = ontologies

    def __eq__(self, other):
        if not isinstance(other, GraphDB):
            return "Not of GraphDB Type"
        else:
            return self.db == other.db

    def __enter__(self) -> GraphDB:
        self.db.initialize()
        self.vector_store.initialize()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.db.save()
        self.vector_store.save()

    def __repr__(self) -> str:
        db_repr = repr(self.db)
        vector_store_repr = repr(self.vector_store)
        graph_generator_repr = repr(self.graph_generator)
        return (
            f"Graph(\n"
            f"  db={db_repr}\n"
            f"  vector_store={vector_store_repr},\n"
            f"  graph_generator={graph_generator_repr}\n"
            f")"
        )

    def _similarity_search_node(
        self,
        text,
        *,
        threshold: float = 0.9,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ):
        use_direct_search = False

        if isinstance(self.vector_store, VliteVSS):
            use_direct_search = True

        elif isinstance(self.vector_store.db, TursoDB) and isinstance(self.db, TursoDB):
            if (
                self.vector_store.db.db_url == self.db.db_url
                and self.vector_store.db.db_auth_token == self.db.db_auth_token
            ):
                use_direct_search = True

        elif isinstance(self.vector_store.db, SQLite) and isinstance(self.db, SQLite):
            if not isinstance(self.vector_store.db, TursoDB) and not isinstance(
                self.db, TursoDB
            ):
                if (
                    self.vector_store.db.local_path == self.db.local_path
                    and self.vector_store.db.local_path is not None
                    and self.db.local_path is not None
                ):
                    use_direct_search = True

        if use_direct_search:
            similar_nodes = self.vector_store.vector_search_node(
                {"body": text},
                threshold=threshold,
                descending=descending,
                limit=limit,
                sort_by=sort_by,
            )
        else:
            similarity_scores = self.vector_store.vector_search_node_from_multi_db(
                {"body": text}, threshold=threshold, limit=limit
            )

            if isinstance(self.vector_store, VliteVSS):
                embed_ids = [
                    attributes["embed_id"]
                    for id, label, attributes, distance in similarity_scores
                ]
            else:
                embed_ids = [score for score, distance in similarity_scores]
            embed_ids_str = json.dumps(embed_ids)

            if embed_ids is None:
                return None

            similar_nodes = self.db.search_similar_nodes(
                embed_ids_str, desc=descending, sort_by=sort_by
            )

        return similar_nodes

    def _similarity_search_edge(
        self,
        text,
        *,
        threshold: float = 0.9,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ):
        use_direct_search = False

        if isinstance(self.vector_store, VliteVSS):
            use_direct_search = True

        elif isinstance(self.vector_store.db, TursoDB) and isinstance(self.db, TursoDB):
            if (
                self.vector_store.db.db_url == self.db.db_url
                and self.vector_store.db.db_auth_token == self.db.db_auth_token
            ):
                use_direct_search = True

        elif isinstance(self.vector_store.db, SQLite) and isinstance(self.db, SQLite):
            if not isinstance(self.vector_store.db, TursoDB) and not isinstance(
                self.db, TursoDB
            ):
                if (
                    self.vector_store.db.local_path == self.db.local_path
                    and self.vector_store.db.local_path is not None
                    and self.db.local_path is not None
                ):
                    use_direct_search = True

        if use_direct_search:
            similar_edges = self.vector_store.vector_search_edge(
                {"body": text},
                threshold=threshold,
                descending=descending,
                limit=limit,
                sort_by=sort_by,
            )
        else:
            similarity_scores = self.vector_store.vector_search_edge_from_multi_db(
                {"body": text}, threshold=threshold, limit=limit
            )
            if isinstance(self.vector_store, VliteVSS):
                embed_ids = [
                    attributes["embed_id"]
                    for id, label, attributes, distance in similarity_scores
                ]
            else:
                embed_ids = [score for score, distance in similarity_scores]

            embed_ids_str = json.dumps(embed_ids)

            if embed_ids is None:
                return None

            similar_edges = self.db.search_similar_edges(
                embed_ids_str, desc=descending, sort_by=sort_by
            )

        return similar_edges

    def insert_node(self, node: Node):
        self.db.add_node(
            node.label,
            json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes,
            node.id,
        )

        self.vector_store.add_node_embedding(
            node.id,
            node.label,
            json.loads(node.attributes)
            if isinstance(node.attributes, str)
            else node.attributes,
        )

    def _add_fhir_node(self, node: Node, node_type: str):
        if not self.db.search_node(node.id):
            self.insert_node(node)
        node_id = str(uuid.uuid4())

        if not self.db.search_node_type(node_type):
            self.db.add_node(node_type, {}, node_id)
            self.vector_store.add_node_embedding(node_id, node_type, {})

        target_node = Node(id=node_id, label=node_type, attributes={})
        edge = EdgeInput(
            source=node,
            target=target_node,
            label="instance_of",
            attributes=node.attributes,
        )
        self.add_edge(edge)

    def _validate_and_add_ontology_node(
        self, node: Node, node_type: Optional[str], ontology: Ontology
    ) -> bool:
        if node_type is None:
            return False

        concept = ontology.search_one(label=node_type)
        if concept is None:
            return False

        if isinstance(node.attributes, dict):
            node_properties = list(node.attributes.keys())
        else:
            node_properties = [node.attributes]

        node_type_properties = self._fetch_ontology_properties(ontology, node_type)

        if node_type_properties != [] and sorted(node_type_properties) != sorted(
            node_properties
        ):
            return False

        if self.db.search_node(node_id=node.id) is None:
            self.insert_node(node)

        node_id = str(uuid.uuid4())
        if not self.db.search_node_type(node_type):
            self.db.add_node(node_type, {}, node_id)
            self.vector_store.add_node_embedding(node_id, node_type, {})

        self.add_node_type(node_id, node_type)

        target_node = Node(id=node_id, label=node_type, attributes={})
        edge = EdgeInput(
            source=node,
            target=target_node,
            label="instance_of",
            attributes=node.attributes,
        )
        self.add_edge(edge)

        return True

    def _fetch_ontology_properties(
        self, ontology: Ontology, node_type: str
    ) -> List[str]:
        node_type_properties = []

        for prop in ontology.properties():
            if prop.domain:
                if prop.domain[0] is not None:
                    if prop.domain[0].name == node_type:
                        node_type_properties.append(prop.name)

        return node_type_properties

    # High level apis
    def add_node_type(self, node_id, node_type) -> None:
        if not self.db.search_node_type(node_type):
            self.db.add_node(node_type, {}, node_id)
            self.vector_store.add_node_embedding(node_id, node_type, {})

    def find_node_type_id(self, node_type) -> str:
        id = self.db.search_id_by_node_type(node_type)
        return id[0]

    def add_node(
        self,
        node: Node,
        *,
        node_type: Optional[str] = None,
        delete_if_properties_not_match: Optional[bool] = False,
    ) -> None:
        if self.ontologies is None:
            if self.db.search_node(node_id=node.id) is None:
                self.insert_node(node)
            return

        valid_ontology_found = False

        for ontology in self.ontologies:
            try:
                if isinstance(ontology, type(fhir)):
                    if node_type and validate_fhir_resource(node_type, node.attributes):
                        self._add_fhir_node(node, node_type)
                        valid_ontology_found = True
                        break
                elif isinstance(ontology, Ontology):
                    if self._validate_and_add_ontology_node(node, node_type, ontology):
                        valid_ontology_found = True
                        break
            except ValueError:
                continue

        if not valid_ontology_found:
            if delete_if_properties_not_match:
                self.db.remove_node(node.id)
            else:
                raise ValueError(
                    "Node type or attributes does not match any of the provided ontologies."
                )

    def add_nodes(
        self,
        nodes: List[Node],
        *,
        node_types: Optional[List[str]] = None,
        delete_if_properties_not_match: Optional[List[bool]] = None,
    ) -> None:
        if self.ontologies is not None:
            if node_types is None:
                raise ValueError("No node types given for the ontology.")

            if len(nodes) != len(node_types):
                raise ValueError("The lengths of the input lists must be equal.")

            if delete_if_properties_not_match is None:
                delete_if_properties_not_match = [False] * len(nodes)

            elif len(delete_if_properties_not_match) != len(nodes):
                raise ValueError(
                    "The length of delete_if_properties_not_match must match the length of nodes if provided."
                )

            for node, node_type, delete_flag in zip(
                nodes, node_types, delete_if_properties_not_match
            ):
                self.add_node(
                    node,
                    node_type=node_type,
                    delete_if_properties_not_match=delete_flag,
                )
        else:
            for node in nodes:
                self.add_node(node)

    def add_edge(self, edge: EdgeInput) -> None:
        attributes = (
            json.loads(edge.attributes)
            if isinstance(edge.attributes, str)
            else edge.attributes
        )
        if (
            self.db.search_edge(edge.source.id, edge.target.id, attributes) is None
            and (self.db.search_node(edge.source.id) is not None)
            and (self.db.search_node(edge.target.id) is not None)
        ):
            self.db.add_edge(
                edge.source.id,
                edge.target.id,
                edge.label,
                json.loads(edge.attributes)
                if isinstance(edge.attributes, str)
                else edge.attributes,
            )
            self.vector_store.add_edge_embedding(
                edge.source.id,
                edge.target.id,
                edge.label,
                json.loads(edge.attributes)
                if isinstance(edge.attributes, str)
                else edge.attributes,
            )

    def add_edges(self, edges: List[EdgeInput]) -> None:
        for edge in edges:
            self.add_edge(edge)

    def update_node(self, node: Node) -> None:
        node_data = self.db.search_node(node.id)
        if node_data is not None:
            embed_id_to_be_updated = self.db.fetch_node_embed_id(node.id)

            node_attributes = (
                json.loads(node.attributes)
                if isinstance(node.attributes, str)
                else node.attributes
            )

            self.db.update_node(node)
            updated_data: Dict = {**node_data, **node_attributes}

            self.vector_store.add_node_embedding(node.id, node.label, updated_data)
            self.vector_store.delete_node_embedding(embed_id_to_be_updated)
        else:
            self.add_node(node)

    def update_nodes(self, nodes: List[Node]) -> None:
        for node in nodes:
            self.update_node(node)

    def remove_node(self, id: Union[str, int]) -> None:
        if self.db.search_node(id) is not None:
            ids = self.db.fetch_edge_embed_ids(id)
            self.vector_store.delete_node_embedding(self.db.fetch_node_embed_id(id))

            self.db.remove_node(id)
            self.vector_store.delete_edge_embedding(ids)

    def remove_nodes(self, ids: List[Any]) -> None:
        for id in ids:
            self.remove_node(id)

    def search_node(self, node_id: str | int) -> Any:
        return self.db.search_node(node_id)

    def search_node_label(self, node_id: str | int) -> Any:
        return self.db.search_node_label(node_id)

    def traverse(
        self, source: str, target: Optional[str] = None, with_bodies: bool = False
    ) -> List:
        return self.db.traverse(source, target, with_bodies)

    def insert_graph(self, kg: KnowledgeGraph) -> KnowledgeGraph:
        uuid_dict = {}

        try:
            for node in kg.nodes:
                uuid_dict[node.id] = str(uuid.uuid4())
                self.db.add_node(
                    node.label,
                    {"body": node.attributes},
                    uuid_dict[node.id],
                )

                self.vector_store.add_node_embedding(
                    uuid_dict[node.id], node.label, {"body": node.attributes}
                )

            for edge in kg.edges:
                self.db.add_edge(
                    uuid_dict[edge.source],
                    uuid_dict[edge.target],
                    edge.label,
                    {"body": edge.attributes},
                )
                self.vector_store.add_edge_embedding(
                    uuid_dict[edge.source],
                    uuid_dict[edge.target],
                    edge.label,
                    {"body": edge.attributes},
                )
        except KeyError:
            return KnowledgeGraph()
        return kg

    def search_from_graph(
        self,
        text: str,
        *,
        threshold: float = 0.9,
        limit: int = 1,
        descending: bool = False,
        sort_by: str = "",
    ) -> KnowledgeGraph:
        try:
            similar_nodes = self._similarity_search_node(
                text,
                threshold=threshold,
                descending=descending,
                limit=limit,
                sort_by=sort_by,
            )
            similar_edges = self._similarity_search_edge(
                text,
                threshold=threshold,
                descending=descending,
                limit=limit,
                sort_by=sort_by,
            )

            resultant_subgraph = KnowledgeGraph()

            if similar_edges and similar_nodes is None or similar_nodes is None:
                return resultant_subgraph

            for node in similar_nodes:
                if isinstance(self.vector_store, VliteVSS):
                    similar_node = Node(
                        id=node[0].rstrip("_0"),
                        label=json.loads(node[1])["label"],
                        attributes=(json.loads(node[1])),
                    )

                else:
                    similar_node = Node(id=node[1], label=node[2], attributes=node[3])
                resultant_subgraph.nodes.append(similar_node)

                nodes = self.db.all_connected_nodes(similar_node)

                if not nodes:
                    continue

                for i in nodes:
                    if i not in resultant_subgraph.nodes:
                        resultant_subgraph.nodes.append(i)

            for edge in similar_edges:
                if isinstance(self.vector_store, VliteVSS):
                    edge = self.search_node(edge[0].rstrip("_0"))

                    if edge is None:
                        continue

                    if "source" not in edge[0][2].keys():
                        continue

                    edge = json.loads(edge[2])

                    similar_edge = Edge(
                        source=edge["source"],
                        target=edge["target"],
                        label=edge["label"],
                        attributes=edge,
                    )
                else:
                    similar_edge = Edge(
                        source=edge[1],
                        target=edge[2],
                        label=edge[3],
                        attributes=edge[4],
                    )
                resultant_subgraph.edges.append(similar_edge)

                nodes = self.db.all_connected_nodes(similar_edge)
                if not nodes:
                    continue

                for node in nodes:
                    if node not in resultant_subgraph.nodes:
                        resultant_subgraph.nodes.append(node)

        except KeyError:
            return KnowledgeGraph()

        return resultant_subgraph

    def merge_by_similarity(self, *, threshold: float = 0.9) -> None:
        node_ids = self.db.fetch_ids_from_db()

        for node_id in node_ids:
            node = self.db.search_node(node_id)
            if node is None:
                continue

            similar_nodes = self._similarity_search_node(
                json.dumps(node), threshold=threshold
            )

            if similar_nodes is None or len(similar_nodes) > 1:
                continue

            for row in similar_nodes:
                similar_node_id = row[1]

                # Skip the same nodes from getting merged
                if similar_node_id is None or similar_node_id == node_id:
                    continue

                in_degree_ids = self.db.search_indegree_edges(similar_node_id)
                out_degree_ids = self.db.search_outdegree_edges(similar_node_id)

                concatenated_attributes: Dict = {}
                concatenated_labels = ""

                for data in in_degree_ids:
                    for key, value in json.loads(data[2]).items():
                        if key in concatenated_attributes:
                            # If the key already exists, update its value
                            concatenated_attributes[key] += value
                        else:
                            # If the key doesn't exist, add a new key-value pair
                            concatenated_attributes[key] = value

                    concatenated_labels += data[1] + ","

                    self.db.add_edge(data[0], node_id, data[1], data[2])
                    self.vector_store.add_edge_embedding(
                        data[0], node_id, data[1], data[2]
                    )

                for data in out_degree_ids:
                    for key, value in json.loads(data[2]).items():
                        if key in concatenated_attributes:
                            # If the key already exists, update its value
                            concatenated_attributes[key] += value
                        else:
                            # If the key doesn't exist, add a new key-value pair
                            concatenated_attributes[key] = value
                    concatenated_labels += data[1] + ","

                    self.db.add_edge(node_id, data[0], data[1], data[2])
                    self.vector_store.add_edge_embedding(
                        node_id, data[0], data[1], data[2]
                    )

                    updated_attributes = node if node else {}
                    updated_attributes.update(concatenated_attributes)
                    new_node_label = self.db.search_node_label(node_id)

                    new_node = Node(
                        id=node_id,
                        label=new_node_label[0] + "," + concatenated_labels,
                        attributes=updated_attributes,
                    )
                    self.update_node(new_node)

                    self.remove_node(similar_node_id)

    def find_nodes_like(self, label: str, *, threshold: float = 0.9) -> List[Node]:
        nodes = self.db.find_nodes_by_label(label)

        similar_rows = []
        for id, text, attribute in nodes:
            similar_nodes = self._similarity_search_node(
                json.dumps(text), threshold=threshold
            )

            if len(similar_nodes) < 1:
                continue

            for rowid in similar_nodes:
                if isinstance(self.vector_store, VliteVSS):
                    fetched_node_id = self.db.fetch_node_id(rowid[0].rstrip("_0"))
                else:
                    fetched_node_id = self.db.fetch_node_id(rowid[0])

                if fetched_node_id is None:
                    continue

                node_data = self.db.search_node(fetched_node_id[0])
                node_label = self.db.search_node_label(fetched_node_id[0])

                if node_data in similar_rows:
                    continue
                node = Node(
                    id=node_data["id"], label=node_label[0], attributes=node_data
                )
                similar_rows.append(node)

        return similar_rows

    def visualize(self, file: str, id: List[str]) -> Digraph:
        return self.db.graphviz_visualize(file, id)

    def fetch_ids_from_db(self) -> List[str]:
        return self.db.fetch_ids_from_db()

    def search_indegree_edges(self, target: str) -> List[Any]:
        return self.db.search_indegree_edges(target)

    def search_outdegree_edges(self, source: str) -> List[Any]:
        return self.db.search_outdegree_edges(source)

    def is_unique_prompt(self, text: str, *, threshold: float = 0.9) -> bool:
        similar_nodes = self._similarity_search_node(text, threshold=threshold, limit=1)

        if not similar_nodes:
            return True

        return False

    def insert(
        self,
        text: str,
        attributes: Dict,
        *,
        node_type: Optional[str] = None,
        delete_if_properties_not_match: Optional[bool] = False,
    ) -> None:
        node = Node(
            id=str(uuid.uuid4()),
            label=text,
            attributes=json.dumps(attributes),
        )
        if self.ontologies is not None:
            self.add_node(
                node,
                node_type=node_type,
                delete_if_properties_not_match=delete_if_properties_not_match,
            )
        else:
            self.add_node(node)

    def search(
        self,
        text: str,
        *,
        threshold: float = 0.9,
        descending: bool = False,
        limit: int = 1,
        sort_by: str = "",
    ) -> None | List[Tuple[Any, str, dict, Any]]:
        similar_nodes = self._similarity_search_node(
            text,
            threshold=threshold,
            descending=descending,
            limit=limit,
            sort_by=sort_by,
        )

        if similar_nodes is None:
            return None

        return similar_nodes
