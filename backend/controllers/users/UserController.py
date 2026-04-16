from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class UserController(IController):
    def register_all_routes(self):
        self.register_route("/api/users", "users_list", self.list_users, "GET")
        self.register_route("/api/users/me", "users_me", self.get_current_user, "GET")
        self.register_route("/api/users/me/orgs", "users_my_orgs", self.list_my_orgs, "GET")
        self.register_route("/api/users/<user_id>/role", "users_update_role", self.update_role, "PUT")
        self.register_route("/api/users/<user_id>", "users_update", self.update_user, "PUT")
        self.register_route("/api/users/<user_id>", "users_delete", self.delete_user, "DELETE")
        self.register_route("/api/users/me/preferences", "users_update_prefs", self.update_preferences, "PUT")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_users(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_users", "page": page, "per_page": per_page},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_current_user(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_current_user"},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_role(self, user_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update_role", "target_user_id": user_id, **data},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_user(self, user_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update_user", "target_user_id": user_id, **data},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_user(self, user_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete_user", "target_user_id": user_id},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def list_my_orgs(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_my_orgs"},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_preferences(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update_preferences", **data},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
