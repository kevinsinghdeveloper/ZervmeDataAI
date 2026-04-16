from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class ReportController(IController):
    def register_all_routes(self):
        self.register_route("/api/reports", "reports_list", self.list_reports, "GET")
        self.register_route("/api/reports", "reports_create", self.create_report, "POST")
        self.register_route("/api/reports/<report_id>", "reports_get", self.get_report, "GET")
        self.register_route("/api/reports/<report_id>", "reports_update", self.update_report, "PUT")
        self.register_route("/api/reports/<report_id>", "reports_delete", self.delete_report, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_reports(self):
        status = request.args.get("status")
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list", "status": status}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_report(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "create", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_report(self, report_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get", "report_id": report_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_report(self, report_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "update", "report_id": report_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_report(self, report_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete", "report_id": report_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
