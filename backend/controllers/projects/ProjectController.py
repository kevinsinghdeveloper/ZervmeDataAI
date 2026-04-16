from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class ProjectController(IController):
    def register_all_routes(self):
        self.register_route("/api/projects", "projects_list", self.list_projects, "GET")
        self.register_route("/api/projects", "projects_create", self.create_project, "POST")
        self.register_route("/api/projects/<project_id>", "projects_get", self.get_project, "GET")
        self.register_route("/api/projects/<project_id>", "projects_update", self.update_project, "PUT")
        self.register_route("/api/projects/<project_id>", "projects_delete", self.delete_project, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_projects(self):
        status = request.args.get("status")
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list", "status": status}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_project(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "create", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_project(self, project_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get", "project_id": project_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_project(self, project_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update", "project_id": project_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_project(self, project_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete", "project_id": project_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
