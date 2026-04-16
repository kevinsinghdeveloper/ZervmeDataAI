from abc import abstractmethod
from typing import Dict, Optional
from abstractions.IServiceManagerBase import IServiceManagerBase
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel


class IResourceManager:
    def __init__(self, service_managers: Optional[Dict[str, IServiceManagerBase]] = None):
        self._service_managers = service_managers or {}

    @property
    def _db(self):
        """Shortcut to the DatabaseService instance."""
        return self._service_managers.get("db")

    @abstractmethod
    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        pass

    @abstractmethod
    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        pass

    @abstractmethod
    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        pass

    @abstractmethod
    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        pass
