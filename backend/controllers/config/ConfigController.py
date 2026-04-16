from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel
from utils.auth_utils import token_required


class ConfigController(IController):
    def register_all_routes(self):
        self.register_route("/api/config/theme", "config_get_theme", self.get_theme, "GET")
        self.register_route("/api/config/theme", "config_update_theme", self.update_theme, "POST")
        self.register_route("/api/config/upload-asset", "config_upload_asset", self.upload_asset, "POST")
        self.register_route("/api/config/first-user", "config_first_user", self.create_first_user, "POST")
        self.register_route("/api/config/settings", "config_get_settings", self.get_settings, "GET")
        self.register_route("/api/config/settings", "config_update_settings", self.update_settings, "POST")

    def get_resource_manager(self):
        return self._resource_manager

    def get_theme(self):
        result = self._resource_manager.get(RequestResourceModel(data={"action": "get_theme"}))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def upload_asset(self):
        file = request.files.get("file")
        asset_type = request.form.get("assetType", "")
        if not file:
            return jsonify({"success": False, "error": "No file provided"}), 400
        file_content = file.read()
        result = self._resource_manager.post(RequestResourceModel(
            data={
                "action": "upload_asset",
                "file_content": file_content,
                "file_name": file.filename or "",
                "asset_type": asset_type,
                "content_type": file.content_type or "application/octet-stream",
            },
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_theme(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "update_theme", **data},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    def create_first_user(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "first_user", **data}
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def get_settings(self):
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "get_settings"},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code

    @token_required
    def update_settings(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "update_settings", **data},
            user_id=request.user_id
        ))
        return jsonify(result.to_dict()), result.status_code
