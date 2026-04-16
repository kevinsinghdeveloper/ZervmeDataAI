from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class AIChatController(IController):
    def register_all_routes(self):
        self.register_route("/api/ai/sessions", "ai_list_sessions", self.list_sessions, "GET")
        self.register_route("/api/ai/sessions", "ai_create_session", self.create_session, "POST")
        self.register_route("/api/ai/sessions/<session_id>", "ai_get_session", self.get_session, "GET")
        self.register_route("/api/ai/sessions/<session_id>", "ai_delete_session", self.delete_session, "DELETE")
        self.register_route("/api/ai/sessions/<session_id>/messages", "ai_list_messages", self.list_messages, "GET")
        self.register_route("/api/ai/sessions/<session_id>/message", "ai_send_message", self.send_message, "POST")
        self.register_route("/api/ai/suggest-entry", "ai_suggest_entry", self.suggest_entry, "POST")
        self.register_route("/api/ai/categorize", "ai_categorize", self.categorize, "POST")
        self.register_route("/api/ai/models", "ai_list_models", self.list_models, "GET")
        self.register_route("/api/ai/models", "ai_update_model", self.update_model, "POST")
        self.register_route("/api/ai/models/<model_id>", "ai_delete_model", self.delete_model, "DELETE")

    def get_resource_manager(self):
        return self._resource_manager

    @token_required
    def list_sessions(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_sessions"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def create_session(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "create_session", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_session(self, session_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_session", "session_id": session_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_session(self, session_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete_session", "session_id": session_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def list_messages(self, session_id):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_messages", "session_id": session_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def send_message(self, session_id):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "send_message", "session_id": session_id, **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def suggest_entry(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "suggest_entry", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def categorize(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "categorize", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def list_models(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "list_models"}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_model(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "update_model_config", **data}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def delete_model(self, model_id):
        result = self._resource_manager.delete(RequestResourceModel(
            data={"action": "delete_model_config", "model_id": model_id}, user_id=request.user_id))
        return jsonify(result.to_dict()), result.status_code
