from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class OrganizationController(IController):
    def register_all_routes(self):
        self.register_route("/api/organizations/current", "org_get_current", self.get_current, "GET")
        self.register_route("/api/organizations/current", "org_update_current", self.update_current, "PUT")
        self.register_route("/api/organizations", "org_create", self.create_organization, "POST")
        self.register_route("/api/organizations/invitations", "org_list_invitations", self.list_invitations, "GET")
        self.register_route("/api/organizations/invitations", "org_create_invitation", self.create_invitation, "POST")
        self.register_route("/api/organizations/invitations/<invitation_id>", "org_delete_invitation", self.delete_invitation, "DELETE")
        self.register_route("/api/organizations/members", "org_list_members", self.list_members, "GET")
        self.register_route("/api/organizations/members/<member_id>/role", "org_update_member_role", self.update_member_role, "PUT")
        self.register_route("/api/organizations/members/<member_id>/roles", "org_list_member_roles", self.list_member_roles, "GET")
        self.register_route("/api/organizations/members/<member_id>/roles", "org_add_member_role", self.add_member_role, "POST")
        self.register_route("/api/organizations/members/<member_id>/roles/<role>", "org_remove_member_role", self.remove_member_role, "DELETE")
        self.register_route("/api/organizations/members/<member_id>", "org_remove_member", self.remove_member, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def get_current(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_current"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_current(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update_current", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_organization(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "create", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def list_invitations(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_invitations"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_invitation(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "create_invitation", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_invitation(self, invitation_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete_invitation", "invitation_id": invitation_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def list_members(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_members"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_member_role(self, member_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update_member_role", "member_id": member_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def list_member_roles(self, member_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_member_roles", "member_id": member_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def add_member_role(self, member_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "add_member_role", "member_id": member_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def remove_member_role(self, member_id, role):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "remove_member_role", "member_id": member_id, "role": role}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def remove_member(self, member_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "remove_member", "member_id": member_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
