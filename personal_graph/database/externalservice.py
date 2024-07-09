from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class ExternalService(ABC):
    """
    Abstract Base Class for implementing external service connections.
    This class inherits from DB and adds methods specific to external service connections.
    """

    @abstractmethod
    def connect(self, url: str):
        """Establish a connection to the external service"""
        pass

    @abstractmethod
    def disconnect(self):
        """Close the connection to the external service"""
        pass

    @abstractmethod
    def execute_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Any:
        """Execute a REST API request to the external service"""
        pass
