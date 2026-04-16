from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class DatasetController(IController):
    def register_all_routes(self):
        self.register_route("/api/datasets", "datasets_list", self.list_datasets, "GET")
        self.register_route("/api/datasets", "datasets_create", self.create_dataset, "POST")
        self.register_route("/api/datasets/<dataset_id>", "datasets_get", self.get_dataset, "GET")
        self.register_route("/api/datasets/<dataset_id>", "datasets_update", self.update_dataset, "PUT")
        self.register_route("/api/datasets/<dataset_id>", "datasets_delete", self.delete_dataset, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_datasets(self):
        status = request.args.get("status")
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list", "status": status}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_dataset(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "create", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_dataset(self, dataset_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get", "dataset_id": dataset_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_dataset(self, dataset_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update", "dataset_id": dataset_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_dataset(self, dataset_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete", "dataset_id": dataset_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
