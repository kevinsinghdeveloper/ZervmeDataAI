from flask import Flask
from abstractions.IController import IController
from abstractions.IResourceManager import IResourceManager


def register_controller(app: Flask, controller_class, resource_manager: IResourceManager):
    controller = controller_class(app, resource_manager)
    controller.register_all_routes()
    return controller
