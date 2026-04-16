from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class NotificationController(IController):
    def register_all_routes(self):
        self.register_route("/api/notifications", "notif_list", self.list_notifications, "GET")
        self.register_route("/api/notifications/<notification_id>/read", "notif_mark_read", self.mark_read, "PUT")
        self.register_route("/api/notifications/read-all", "notif_read_all", self.read_all, "POST")
        self.register_route("/api/notifications/unread-count", "notif_unread", self.unread_count, "GET")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_notifications(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def mark_read(self, notification_id):
        result = self._resource_manager.put(RequestResourceModel(
            data={"action": "mark_read", "notification_id": notification_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def read_all(self):
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "read_all"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def unread_count(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "unread_count"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
