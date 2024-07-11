from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List, Union


class ExternalService(ABC):
    """
    Abstract Base Class for implementing external service connections.
    This class inherits from DB and adds methods specific to external service connections.
    """

    @abstractmethod
    def disconnect(self):
        """Close the connection to the external service"""
        pass

    @abstractmethod
    def execute_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        """Execute a REST API request to the external service"""
        pass

    @abstractmethod
    def set_ontologies(self, ontologies: Optional[List[Any]] = None):
        """Set the ontologies for the service"""
        pass

    @abstractmethod
    def add_node(self, label: str, attribute: Dict, db_url: str):
        """Add a node to the service."""
        pass

    @abstractmethod
    def remove_node(self, id: Union[str, int], db_url: str, resource_type: str):
        """Remove a node from the service."""
        pass

    @abstractmethod
    def search_node(self, node_id: Union[str, int], db_url: str, resource_type: str):
        """Search for a node in the service"""
        pass

    @abstractmethod
    def update_node(self, node: Any, db_url: str):
        """Update a node in the service"""
        pass
