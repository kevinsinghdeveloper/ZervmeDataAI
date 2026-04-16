from abc import abstractmethod
from flask import Flask
from abstractions.IResourceManager import IResourceManager


class IController:
    def __init__(self, app: Flask, resource_manager: IResourceManager):
        self.__app = app
        self._resource_manager = resource_manager

    @abstractmethod
    def register_all_routes(self):
        pass

    def register_route(self, api_rule, api_endpoint, func, method: str):
        self.__app.add_url_rule(api_rule, api_endpoint, func, methods=[method])

    @abstractmethod
    def get_resource_manager(self):
        pass
