"""Legacy Admin Controller - kept for backward compatibility.
New admin functionality is in SuperAdminController, OrganizationController, etc.
"""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class AdminController(IController):
    def register_all_routes(self):
        self.register_route("/api/admin/dashboard", "admin_dashboard", self.get_dashboard, "GET")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def get_dashboard(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "dashboard"},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
