"""Dashboard Controller - read-only endpoints for report dashboard data."""
from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class DashboardController(IController):
    def register_all_routes(self):
        self.register_route(
            "/api/dashboard/report/<report_id>",
            "dashboard_report",
            self.get_dashboard_for_report,
            "GET",
        )
        self.register_route(
            "/api/dashboard/overview",
            "dashboard_overview",
            self.get_dashboard_overview,
            "GET",
        )

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def get_dashboard_for_report(self, report_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_report_dashboard", "report_id": report_id},
            user_id=request.user_id,
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_dashboard_overview(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_overview"},
            user_id=request.user_id,
        ))
        return jsonify(result.to_dict()), result.status_code
