from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class AuditController(IController):
    def register_all_routes(self):
        self.register_route("/api/audit/logs", "audit_logs", self.get_audit_logs, "GET")
        self.register_route("/api/audit/logs/<log_id>", "audit_log_detail", self.get_audit_log, "GET")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def get_audit_logs(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        action_filter = request.args.get("action")
        user_filter = request.args.get("user_id")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        result = self._resource_manager.get(RequestResourceModel(
            data={
                "action": "list_logs",
                "page": page,
                "per_page": per_page,
                "action_filter": action_filter,
                "user_filter": user_filter,
                "start_date": start_date,
                "end_date": end_date,
            },
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_audit_log(self, log_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_log", "log_id": log_id},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
