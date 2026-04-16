from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class ModelConfigController(IController):
    def register_all_routes(self):
        self.register_route("/api/model-configs", "model_configs_list", self.list_model_configs, "GET")
        self.register_route("/api/model-configs", "model_configs_create", self.create_model_config, "POST")
        self.register_route("/api/model-configs/<config_id>", "model_configs_get", self.get_model_config, "GET")
        self.register_route("/api/model-configs/<config_id>", "model_configs_update", self.update_model_config, "PUT")
        self.register_route("/api/model-configs/<config_id>", "model_configs_delete", self.delete_model_config, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_model_configs(self):
        status = request.args.get("status")
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list", "status": status}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_model_config(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "create", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_model_config(self, config_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get", "config_id": config_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_model_config(self, config_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update", "config_id": config_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_model_config(self, config_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete", "config_id": config_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
