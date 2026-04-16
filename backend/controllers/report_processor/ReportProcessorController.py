from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class ReportProcessorController(IController):
    def register_all_routes(self):
        self.register_route("/api/report-processor/start", "report_processor_start", self.start_job, "POST")
        self.register_route("/api/report-processor/status/<job_id>", "report_processor_status", self.get_status, "GET")
        self.register_route("/api/report-processor/stop/<job_id>", "report_processor_stop", self.stop_job, "POST")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def start_job(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "start_job", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_status(self, job_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_status", "job_id": job_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def stop_job(self, job_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "stop_job", "job_id": job_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
