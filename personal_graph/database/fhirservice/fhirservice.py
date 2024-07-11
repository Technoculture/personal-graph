import json
import requests
from fastapi import HTTPException
from typing import List, Any, Dict, Optional, Union

from personal_graph import Node
from personal_graph.database.externalservice import ExternalService


class FhirService(ExternalService):
    def __init__(self, url: str):
        self.base_url = url
        self.session = requests.Session()

    def __repr__(self) -> str:
        return f"  FhirService(\n" f"  url={self.base_url},\n" f"  )"

    def set_ontologies(self, ontologies: Optional[List[Any]] = None):
        if not ontologies:
            raise ValueError("Ontology not provided")
        self.ontologies = ontologies

    def disconnect(self):
        self.session.close()

    def execute_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.request(method, url, json=data, params=params)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 422:
                raise HTTPException(
                    status_code=422,
                    detail="Validation error: " + str(e.response.json()),
                )
            else:
                raise

    def add_node(self, label: str, attribute: Dict, db_url: str):
        try:
            params = {
                "db_url": db_url,
                "resource_type": label,
            }

            response = self.execute_request(
                method="POST", endpoint=label, data=attribute, params=params
            )
            return response
        except requests.HTTPError as e:
            if e.response.status_code == 422:
                error_detail = e.response.json()
                raise HTTPException(
                    status_code=422, detail="Validation error: " + str(error_detail)
                )
            else:
                raise

    def remove_node(self, id: Union[str, int], db_url: str, resource_type: str):
        params = {
            "db_url": db_url,
            "resource_type": resource_type,
            "resource_id": id,
        }
        return self.execute_request(
            method="DELETE", endpoint=f"{resource_type}/{id}", params=params
        )

    def search_node(self, node_id: Union[str, int], db_url: str, resource_type: str):
        # Search for a resource by its ID across all resource types
        try:
            params = {
                "db_url": db_url,
                "resource_type": resource_type,
                "resource_id": node_id,
            }
            response = self.execute_request(
                "GET", f"{resource_type}/{node_id}", params=params
            )
            return response

        except requests.HTTPError:
            raise

    def update_node(self, node: Node, db_url: str):
        resource_type = node.label
        params = {
            "db_url": db_url,
            "resource_type": resource_type,
            "resource_id": node.id,
        }

        if isinstance(node.attributes, str):
            attributes = json.loads(node.attributes)
        else:
            attributes = node.attributes

        return self.execute_request(
            "PUT", f"{resource_type}/{node.id}", data=attributes, params=params
        )
