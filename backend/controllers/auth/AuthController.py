from flask import request, jsonify
from abstractions.IController import IController
from abstractions.models.RequestResourceModel import RequestResourceModel


class AuthController(IController):
    def register_all_routes(self):
        self.register_route("/api/auth/register", "auth_register", self.register, "POST")
        self.register_route("/api/auth/login", "auth_login", self.login, "POST")
        self.register_route("/api/auth/logout", "auth_logout", self.logout, "POST")
        self.register_route("/api/auth/refresh", "auth_refresh", self.refresh, "POST")
        self.register_route("/api/auth/verify-email", "auth_verify_email", self.verify_email, "POST")
        self.register_route("/api/auth/forgot-password", "auth_forgot_password", self.forgot_password, "POST")
        self.register_route("/api/auth/reset-password", "auth_reset_password", self.reset_password, "POST")
        self.register_route("/api/auth/challenge", "auth_challenge", self.respond_to_challenge, "POST")
        self.register_route("/api/auth/accept-invitation", "auth_accept_invitation", self.accept_invitation, "POST")
        # OAuth routes
        self.register_route("/api/auth/oauth/<provider>/authorize", "auth_oauth_authorize", self.oauth_authorize, "GET")
        self.register_route("/api/auth/oauth/<provider>/callback", "auth_oauth_callback", self.oauth_callback, "POST")

    def get_resource_manager(self):
        return self._resource_manager

    def register(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data={"action": "register", **data}))
        return jsonify(result.to_dict()), result.status_code

    def login(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data={"action": "login", **data}))
        return jsonify(result.to_dict()), result.status_code

    def logout(self):
        result = self._resource_manager.post(RequestResourceModel(data={"action": "logout"}))
        return jsonify(result.to_dict()), result.status_code

    def refresh(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data={"action": "refresh", **data}))
        return jsonify(result.to_dict()), result.status_code

    def verify_email(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.get(RequestResourceModel(data={"action": "verify_email", **data}))
        return jsonify(result.to_dict()), result.status_code

    def forgot_password(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data={"action": "forgot_password", **data}))
        return jsonify(result.to_dict()), result.status_code

    def reset_password(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data={"action": "reset_password", **data}))
        return jsonify(result.to_dict()), result.status_code

    def respond_to_challenge(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data={"action": "respond_to_challenge", **data}))
        return jsonify(result.to_dict()), result.status_code

    def accept_invitation(self):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(data={"action": "accept_invitation", **data}))
        return jsonify(result.to_dict()), result.status_code

    def oauth_authorize(self, provider):
        redirect_uri = request.args.get("redirect_uri", "")
        result = self._resource_manager.get(RequestResourceModel(
            data={"action": "oauth_authorize", "provider": provider, "redirect_uri": redirect_uri}))
        return jsonify(result.to_dict()), result.status_code

    def oauth_callback(self, provider):
        data = request.get_json(force=True, silent=True) or {}
        result = self._resource_manager.post(RequestResourceModel(
            data={"action": "oauth_callback", "provider": provider, **data}))
        return jsonify(result.to_dict()), result.status_code
