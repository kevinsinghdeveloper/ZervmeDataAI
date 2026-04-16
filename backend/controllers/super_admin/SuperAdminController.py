from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class SuperAdminController(IController):
    def register_all_routes(self):
        self.register_route("/api/super-admin/organizations", "sa_orgs", self.list_organizations, "GET")
        self.register_route("/api/super-admin/users", "sa_users", self.list_users, "GET")
        self.register_route("/api/super-admin/stats", "sa_stats", self.get_stats, "GET")
        self.register_route("/api/super-admin/organizations/<org_id>", "sa_update_org", self.update_organization, "PUT")
        self.register_route("/api/super-admin/users/<user_id>/toggle", "sa_toggle_user", self.toggle_user, "PUT")
        self.register_route("/api/super-admin/users/<user_id>/reset-password", "sa_reset_password", self.reset_password, "POST")
        self.register_route("/api/super-admin/grant-super-admin", "sa_grant_super_admin", self.grant_super_admin, "POST")
        self.register_route("/api/super-admin/revoke-super-admin", "sa_revoke_super_admin", self.revoke_super_admin, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_organizations(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_organizations", "page": page, "per_page": per_page}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def list_users(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_users", "page": page, "per_page": per_page}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_stats(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "stats"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_organization(self, org_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update_organization", "org_id": org_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def toggle_user(self, user_id):
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "toggle_user", "target_user_id": user_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def reset_password(self, user_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "reset_password", "target_user_id": user_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def grant_super_admin(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "grant_super_admin", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def revoke_super_admin(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "revoke_super_admin", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
