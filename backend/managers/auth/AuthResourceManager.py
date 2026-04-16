"""Auth Resource Manager - uses AWS Cognito for authentication."""
import os
import json
import uuid
import hashlib
import hmac
import secrets
import boto3
from datetime import datetime
from flask import request as flask_request
from botocore.exceptions import ClientError

from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.user import UserItem
from database.schemas.audit_log import AuditLogItem
from database.schemas.organization import OrganizationItem
from database.schemas.org_invitation import OrgInvitationItem
from utils.user_role_service import grant_role, get_user_org_memberships, is_super_admin

COGNITO_REGION = os.getenv("AWS_REGION_NAME", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")
OAUTH_INTERNAL_SECRET = os.getenv("OAUTH_INTERNAL_SECRET", "zerve-oauth-internal-key-change-me")


def _get_cognito_client():
    return boto3.client("cognito-idp", region_name=COGNITO_REGION)


class AuthResourceManager(IResourceManager):

    def __init__(self, service_managers=None):
        super().__init__(service_managers)
        self.cognito = _get_cognito_client()

    @staticmethod
    def _generate_oauth_password(email: str) -> str:
        """Generate a deterministic internal password for OAuth users.

        Uses HMAC-SHA256 with an internal secret so the password is consistent
        across logins but not guessable without the secret.
        """
        digest = hmac.new(
            OAUTH_INTERNAL_SECRET.encode("utf-8"),
            email.lower().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        # Ensure it meets Cognito password policy: uppercase + lowercase + digit + 8+ chars
        return f"Oa{digest[:30]}!1"

    def _get_cognito_tokens_for_oauth_user(self, email: str) -> dict:
        """Set a deterministic password for an OAuth user and get Cognito tokens.

        Returns dict with IdToken, AccessToken, RefreshToken or raises on failure.
        """
        password = self._generate_oauth_password(email)
        self.cognito.admin_set_user_password(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email,
            Password=password,
            Permanent=True,
        )
        auth_response = self.cognito.admin_initiate_auth(
            UserPoolId=COGNITO_USER_POOL_ID,
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
            },
        )
        return auth_response.get("AuthenticationResult", {})

    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action", "")
        if action == "verify_email":
            return self._verify_email(request_resource_model)
        elif action == "oauth_authorize":
            return self._oauth_authorize(request_resource_model)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action", "")
        if action == "register":
            return self._register(request_resource_model)
        elif action == "login":
            return self._login(request_resource_model)
        elif action == "logout":
            return self._logout(request_resource_model)
        elif action == "refresh":
            return self._refresh(request_resource_model)
        elif action == "forgot_password":
            return self._forgot_password(request_resource_model)
        elif action == "reset_password":
            return self._reset_password(request_resource_model)
        elif action == "respond_to_challenge":
            return self._respond_to_challenge(request_resource_model)
        elif action == "accept_invitation":
            return self._accept_invitation(request_resource_model)
        elif action == "oauth_callback":
            return self._oauth_callback(request_resource_model)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Not implemented", status_code=405)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Not implemented", status_code=405)

    def _register(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            first_name = data.get("firstName", "")
            last_name = data.get("lastName", "")
            invitation_token = data.get("invitationToken", "")

            if not email or not password:
                return ResponseModel(success=False, error="Email and password are required", status_code=400)
            if len(password) < 8:
                return ResponseModel(success=False, error="Password must be at least 8 characters", status_code=400)

            # If invitation token provided, validate it first
            invite = None
            if invitation_token:
                from boto3.dynamodb.conditions import Key as CondKey
                resp = self._db.org_invitations.raw_query(
                    IndexName="TokenIndex",
                    KeyConditionExpression=CondKey("token").eq(invitation_token),
                )
                inv_items = resp.get("Items", [])
                if inv_items:
                    invite = OrgInvitationItem.from_item(inv_items[0])
                    if invite.status != "pending":
                        invite = None  # Invitation already used, proceed with normal registration

            try:
                signup_response = self.cognito.sign_up(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email,
                    Password=password,
                    UserAttributes=[
                        {"Name": "email", "Value": email},
                        {"Name": "given_name", "Value": first_name},
                        {"Name": "family_name", "Value": last_name},
                    ],
                )
                cognito_sub = signup_response["UserSub"]

                try:
                    self.cognito.admin_confirm_sign_up(
                        UserPoolId=COGNITO_USER_POOL_ID,
                        Username=email,
                    )
                    self.cognito.admin_update_user_attributes(
                        UserPoolId=COGNITO_USER_POOL_ID,
                        Username=email,
                        UserAttributes=[
                            {"Name": "email_verified", "Value": "true"},
                        ],
                    )
                except ClientError:
                    pass

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "UsernameExistsException":
                    return ResponseModel(success=False, error="Email already registered", status_code=409)
                elif error_code == "InvalidPasswordException":
                    return ResponseModel(success=False, error="Password does not meet requirements", status_code=400)
                return ResponseModel(success=False, error=str(e.response["Error"]["Message"]), status_code=400)

            # Check if first user (auto-admin)
            scan_result = self._db.users.raw_scan(Limit=1, Select="COUNT")
            is_first_user = scan_result.get("Count", 0) == 0

            # Determine org linkage from invitation
            org_id = None
            org_role = "owner" if is_first_user else "member"
            if invite and not is_first_user:
                org_id = invite.org_id
                org_role = invite.role

            user = UserItem(
                id=cognito_sub,
                email=email,
                first_name=first_name,
                last_name=last_name,
                org_id=org_id,
                role="admin" if is_first_user else "member",
                org_role=org_role,
                is_super_admin=is_first_user,
                is_active=True,
                is_verified=True,
                status="active",
            )
            self._db.users.create(user.to_item())

            # Dual-write: create role entries in user_roles table
            if is_first_user:
                grant_role(user_id=cognito_sub, org_id="GLOBAL", role="super_admin", granted_by="system")
            if org_id and org_role:
                grant_role(user_id=cognito_sub, org_id=org_id, role=org_role, granted_by="system")

            # If invitation was used, mark it accepted and increment org member count
            if invite:
                self._db.org_invitations.raw_update_item(
                    Key={"id": invite.id},
                    UpdateExpression="SET #s = :s, accepted_at = :a",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={":s": "accepted", ":a": datetime.utcnow().isoformat()},
                )
                self._db.organizations.raw_update_item(
                    Key={"id": invite.org_id},
                    UpdateExpression="SET member_count = if_not_exists(member_count, :zero) + :inc, updated_at = :u",
                    ExpressionAttributeValues={
                        ":inc": 1,
                        ":zero": 0,
                        ":u": datetime.utcnow().isoformat(),
                    },
                )

            audit = AuditLogItem(
                user_id=cognito_sub,
                action="user_registered",
                resource="auth",
                details=json.dumps({"email": email, "is_first_user": is_first_user, "invitation": bool(invite)}),
                ip_address=flask_request.remote_addr if flask_request else None,
            )
            self._db.audit_logs.create(audit.to_item())

            user_dict = user.to_api_dict()
            user_dict["isSuperAdmin"] = is_super_admin(cognito_sub)
            user_dict["orgMemberships"] = get_user_org_memberships(cognito_sub)

            return ResponseModel(
                success=True,
                data={"user": user_dict, "requiresVerification": False},
                message="Registration successful.",
                status_code=201,
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"Registration failed: {str(e)}", status_code=500)

    def _login(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")

            if not email or not password:
                return ResponseModel(success=False, error="Email and password are required", status_code=400)

            try:
                auth_response = self.cognito.initiate_auth(
                    ClientId=COGNITO_CLIENT_ID,
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters={
                        "USERNAME": email,
                        "PASSWORD": password,
                    },
                )
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code in ("NotAuthorizedException", "UserNotFoundException"):
                    return ResponseModel(success=False, error="Invalid email or password", status_code=401)
                elif error_code == "UserNotConfirmedException":
                    return ResponseModel(success=False, error="Please verify your email first", status_code=403)
                return ResponseModel(success=False, error=str(e.response["Error"]["Message"]), status_code=401)

            # Check for NEW_PASSWORD_REQUIRED challenge
            challenge_name = auth_response.get("ChallengeName")
            if challenge_name == "NEW_PASSWORD_REQUIRED":
                session = auth_response.get("Session", "")
                return ResponseModel(
                    success=True,
                    data={
                        "challengeName": "NEW_PASSWORD_REQUIRED",
                        "session": session,
                        "email": email,
                    },
                    message="Password change required",
                    status_code=200,
                )

            auth_result = auth_response.get("AuthenticationResult", {})
            id_token = auth_result.get("IdToken", "")
            access_token = auth_result.get("AccessToken", "")
            refresh_token = auth_result.get("RefreshToken", "")

            # Get user profile from DynamoDB
            import jwt as pyjwt
            decoded = pyjwt.decode(id_token, options={"verify_signature": False})
            cognito_sub = decoded.get("sub", "")

            user_item = self._db.users.raw_get_item({"id": cognito_sub})

            if not user_item:
                user = UserItem(
                    id=cognito_sub,
                    email=email,
                    first_name=decoded.get("given_name", ""),
                    last_name=decoded.get("family_name", ""),
                    is_verified=True,
                    status="active",
                )
                self._db.users.create(user.to_item())
                user_item = user.to_item()

            user = UserItem.from_item(user_item)

            if not user.is_active:
                return ResponseModel(success=False, error="Account is deactivated", status_code=403)

            # Audit log
            audit = AuditLogItem(
                user_id=cognito_sub,
                action="user_login",
                resource="auth",
                details=json.dumps({"email": email}),
                ip_address=flask_request.remote_addr if flask_request else None,
            )
            self._db.audit_logs.create(audit.to_item())

            user_dict = user.to_api_dict()
            user_dict["isSuperAdmin"] = is_super_admin(user.id)
            user_dict["orgMemberships"] = get_user_org_memberships(user.id)

            return ResponseModel(
                success=True,
                data={
                    "user": user_dict,
                    "accessToken": id_token,
                    "refreshToken": refresh_token,
                    "token": id_token,
                },
                message="Login successful",
                status_code=200,
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"Login failed: {str(e)}", status_code=500)

    def _respond_to_challenge(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Handle NEW_PASSWORD_REQUIRED challenge response."""
        try:
            data = request_resource_model.data
            email = data.get("email", "").strip().lower()
            new_password = data.get("newPassword", "")
            session = data.get("session", "")

            if not email or not new_password or not session:
                return ResponseModel(
                    success=False,
                    error="Email, new password, and session are required",
                    status_code=400,
                )

            if len(new_password) < 8:
                return ResponseModel(success=False, error="Password must be at least 8 characters", status_code=400)

            try:
                challenge_response = self.cognito.respond_to_auth_challenge(
                    ClientId=COGNITO_CLIENT_ID,
                    ChallengeName="NEW_PASSWORD_REQUIRED",
                    Session=session,
                    ChallengeResponses={
                        "USERNAME": email,
                        "NEW_PASSWORD": new_password,
                    },
                )
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "InvalidPasswordException":
                    return ResponseModel(success=False, error="Password does not meet requirements", status_code=400)
                if error_code == "NotAuthorizedException":
                    return ResponseModel(success=False, error="Session expired. Please log in again.", status_code=401)
                return ResponseModel(success=False, error=str(e.response["Error"]["Message"]), status_code=400)

            auth_result = challenge_response.get("AuthenticationResult", {})
            id_token = auth_result.get("IdToken", "")
            refresh_token = auth_result.get("RefreshToken", "")

            if not id_token:
                return ResponseModel(success=False, error="Failed to get tokens after password change", status_code=500)

            # Get user profile
            import jwt as pyjwt
            decoded = pyjwt.decode(id_token, options={"verify_signature": False})
            cognito_sub = decoded.get("sub", "")

            user_item = self._db.users.raw_get_item({"id": cognito_sub})

            if user_item:
                # Update must_reset_password and status
                self._db.users.raw_update_item(
                    Key={"id": cognito_sub},
                    UpdateExpression="SET must_reset_password = :mrp, #s = :s, updated_at = :u",
                    ExpressionAttributeNames={"#s": "status"},
                    ExpressionAttributeValues={
                        ":mrp": False, ":s": "active",
                        ":u": datetime.utcnow().isoformat(),
                    },
                )
                user_item["must_reset_password"] = False
                user_item["status"] = "active"

            user = UserItem.from_item(user_item) if user_item else UserItem(
                id=cognito_sub, email=email, is_verified=True, status="active",
            )

            audit = AuditLogItem(
                user_id=cognito_sub,
                action="password_reset_challenge",
                resource="auth",
                details=json.dumps({"email": email}),
                ip_address=flask_request.remote_addr if flask_request else None,
            )
            self._db.audit_logs.create(audit.to_item())

            return ResponseModel(
                success=True,
                data={
                    "user": user.to_api_dict(),
                    "accessToken": id_token,
                    "refreshToken": refresh_token,
                    "token": id_token,
                },
                message="Password changed successfully",
                status_code=200,
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"Challenge response failed: {str(e)}", status_code=500)

    def _logout(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=True, message="Logged out successfully", status_code=200)

    def _refresh(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data
            refresh_token = data.get("refreshToken", "")

            if not refresh_token:
                return ResponseModel(success=False, error="Refresh token is required", status_code=400)

            try:
                auth_response = self.cognito.initiate_auth(
                    ClientId=COGNITO_CLIENT_ID,
                    AuthFlow="REFRESH_TOKEN_AUTH",
                    AuthParameters={"REFRESH_TOKEN": refresh_token},
                )
            except ClientError as e:
                return ResponseModel(success=False, error="Invalid refresh token", status_code=401)

            auth_result = auth_response.get("AuthenticationResult", {})
            return ResponseModel(
                success=True,
                data={
                    "accessToken": auth_result.get("IdToken", ""),
                    "token": auth_result.get("IdToken", ""),
                },
                message="Token refreshed",
                status_code=200,
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"Token refresh failed: {str(e)}", status_code=500)

    def _verify_email(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data
            email = data.get("email", "").strip().lower()
            code = data.get("code", "")

            if not email or not code:
                return ResponseModel(success=False, error="Email and verification code are required", status_code=400)

            try:
                self.cognito.confirm_sign_up(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email,
                    ConfirmationCode=code,
                )
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "CodeMismatchException":
                    return ResponseModel(success=False, error="Invalid verification code", status_code=400)
                elif error_code == "ExpiredCodeException":
                    return ResponseModel(success=False, error="Verification code has expired", status_code=400)
                return ResponseModel(success=False, error=str(e.response["Error"]["Message"]), status_code=400)

            user = self._db.users.find_by_email(email)
            if user:
                self._db.users.raw_update_item(
                    Key={"id": user.id},
                    UpdateExpression="SET is_verified = :v, updated_at = :u",
                    ExpressionAttributeValues={":v": True, ":u": datetime.utcnow().isoformat()},
                )

            return ResponseModel(success=True, message="Email verified successfully", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Verification failed: {str(e)}", status_code=500)

    def _forgot_password(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data
            email = data.get("email", "").strip().lower()

            if not email:
                return ResponseModel(success=False, error="Email is required", status_code=400)

            try:
                self.cognito.forgot_password(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email,
                )
            except ClientError:
                pass

            return ResponseModel(
                success=True,
                message="If the email exists, a password reset code has been sent.",
                status_code=200,
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"Password reset request failed: {str(e)}", status_code=500)

    def _reset_password(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            data = request_resource_model.data
            email = data.get("email", "").strip().lower()
            code = data.get("code", "")
            new_password = data.get("newPassword", "")

            if not email or not code or not new_password:
                return ResponseModel(success=False, error="Email, code, and new password are required", status_code=400)

            try:
                self.cognito.confirm_forgot_password(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email,
                    ConfirmationCode=code,
                    Password=new_password,
                )
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "CodeMismatchException":
                    return ResponseModel(success=False, error="Invalid reset code", status_code=400)
                elif error_code == "ExpiredCodeException":
                    return ResponseModel(success=False, error="Reset code has expired", status_code=400)
                return ResponseModel(success=False, error=str(e.response["Error"]["Message"]), status_code=400)

            return ResponseModel(success=True, message="Password reset successfully", status_code=200)
        except Exception as e:
            return ResponseModel(success=False, error=f"Password reset failed: {str(e)}", status_code=500)

    def _accept_invitation(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Accept an org invitation by token. If user_id is provided, link user to org."""
        try:
            data = request_resource_model.data
            token = data.get("token", "")
            user_id = request_resource_model.user_id  # Set if authenticated
            if not token:
                return ResponseModel(success=False, error="Invitation token is required", status_code=400)

            # Look up invitation
            from boto3.dynamodb.conditions import Key
            resp = self._db.org_invitations.raw_query(
                IndexName="TokenIndex",
                KeyConditionExpression=Key("token").eq(token),
            )
            items = resp.get("Items", [])
            if not items:
                return ResponseModel(success=False, error="Invalid or expired invitation", status_code=404)

            invite = OrgInvitationItem.from_item(items[0])
            if invite.status != "pending":
                return ResponseModel(success=False, error="Invitation already used", status_code=400)

            # Mark invitation accepted
            self._db.org_invitations.raw_update_item(
                Key={"id": invite.id},
                UpdateExpression="SET #s = :s, accepted_at = :a",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": "accepted", ":a": datetime.utcnow().isoformat()},
            )

            # If authenticated user, link them to the org
            if user_id:
                # Dual-write: user record (backward compat) + user_roles table
                self._db.users.raw_update_item(
                    Key={"id": user_id},
                    UpdateExpression="SET org_id = :oid, org_role = :role, updated_at = :u",
                    ExpressionAttributeValues={
                        ":oid": invite.org_id,
                        ":role": invite.role,
                        ":u": datetime.utcnow().isoformat(),
                    },
                )
                grant_role(
                    user_id=user_id,
                    org_id=invite.org_id,
                    role=invite.role,
                    granted_by=invite.invited_by,
                )
                # Increment org member_count
                self._db.organizations.raw_update_item(
                    Key={"id": invite.org_id},
                    UpdateExpression="SET member_count = if_not_exists(member_count, :zero) + :inc, updated_at = :u",
                    ExpressionAttributeValues={
                        ":inc": 1,
                        ":zero": 0,
                        ":u": datetime.utcnow().isoformat(),
                    },
                )

            return ResponseModel(
                success=True,
                data={"orgId": invite.org_id, "role": invite.role, "email": invite.email},
                message="Invitation accepted",
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"Accept invitation failed: {str(e)}", status_code=500)

    def _oauth_authorize(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Get OAuth authorization URL for a provider."""
        try:
            provider_name = request_resource_model.data.get("provider", "")
            redirect_uri = request_resource_model.data.get("redirect_uri", "")

            oauth_manager = self._service_managers.get("oauth")
            if not oauth_manager:
                return ResponseModel(success=False, error="OAuth not configured", status_code=503)

            provider = oauth_manager.get_provider(provider_name)
            if not provider:
                return ResponseModel(success=False, error=f"Provider '{provider_name}' not available", status_code=404)

            import uuid
            state = str(uuid.uuid4())
            url = provider.get_authorization_url(redirect_uri, state)
            return ResponseModel(success=True, data={"url": url, "state": state})
        except Exception as e:
            return ResponseModel(success=False, error=f"OAuth authorize failed: {str(e)}", status_code=500)

    def _oauth_callback(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """Handle OAuth callback - exchange code, get/create user, return tokens."""
        try:
            data = request_resource_model.data
            provider_name = data.get("provider", "")
            code = data.get("code", "")
            redirect_uri = data.get("redirect_uri", "")

            if not code:
                return ResponseModel(success=False, error="Authorization code is required", status_code=400)

            oauth_manager = self._service_managers.get("oauth")
            if not oauth_manager:
                return ResponseModel(success=False, error="OAuth not configured", status_code=503)

            provider = oauth_manager.get_provider(provider_name)
            if not provider:
                return ResponseModel(success=False, error=f"Provider '{provider_name}' not available", status_code=404)

            # Exchange code for tokens
            tokens = provider.exchange_code_for_tokens(code, redirect_uri)
            user_info = provider.get_user_info(tokens.access_token)

            # Check if user exists by email
            existing_user = self._db.users.find_by_email(user_info.email)

            if existing_user:
                # Existing user - link provider and log in
                user = existing_user
                oauth_providers = json.loads(user.oauth_providers) if user.oauth_providers else {}
                oauth_providers[provider_name] = {
                    "provider_user_id": user_info.provider_user_id,
                    "linked_at": datetime.utcnow().isoformat(),
                }
                self._db.users.raw_update_item(
                    Key={"id": user.id},
                    UpdateExpression="SET oauth_providers = :op, updated_at = :u",
                    ExpressionAttributeValues={
                        ":op": json.dumps(oauth_providers),
                        ":u": datetime.utcnow().isoformat(),
                    },
                )
            else:
                # New user - create in Cognito + DynamoDB
                oauth_password = self._generate_oauth_password(user_info.email)
                try:
                    signup_resp = self.cognito.admin_create_user(
                        UserPoolId=COGNITO_USER_POOL_ID,
                        Username=user_info.email,
                        UserAttributes=[
                            {"Name": "email", "Value": user_info.email},
                            {"Name": "email_verified", "Value": "true"},
                            {"Name": "given_name", "Value": user_info.first_name or ""},
                            {"Name": "family_name", "Value": user_info.last_name or ""},
                        ],
                        MessageAction="SUPPRESS",
                    )
                    cognito_sub = signup_resp["User"]["Attributes"]
                    cognito_sub = next((a["Value"] for a in cognito_sub if a["Name"] == "sub"), str(uuid.uuid4()))
                    self.cognito.admin_set_user_password(
                        UserPoolId=COGNITO_USER_POOL_ID,
                        Username=user_info.email,
                        Password=oauth_password,
                        Permanent=True,
                    )
                except ClientError:
                    cognito_sub = str(uuid.uuid4())

                oauth_providers = {provider_name: {
                    "provider_user_id": user_info.provider_user_id,
                    "linked_at": datetime.utcnow().isoformat(),
                }}
                user = UserItem(
                    id=cognito_sub,
                    email=user_info.email,
                    first_name=user_info.first_name,
                    last_name=user_info.last_name,
                    avatar_url=user_info.avatar_url,
                    is_verified=True,
                    status="active",
                    oauth_providers=json.dumps(oauth_providers),
                )
                self._db.users.create(user.to_item())

            # Generate Cognito JWT tokens for the OAuth user
            try:
                auth_result = self._get_cognito_tokens_for_oauth_user(user_info.email)
                id_token = auth_result.get("IdToken", "")
                refresh_token = auth_result.get("RefreshToken", "")

                if not id_token:
                    return ResponseModel(
                        success=False,
                        error="Failed to generate authentication tokens",
                        status_code=500,
                    )
            except ClientError as e:
                return ResponseModel(
                    success=False,
                    error=f"Token generation failed: {e.response['Error']['Message']}",
                    status_code=500,
                )

            # Audit log
            audit = AuditLogItem(
                user_id=user.id,
                action="user_oauth_login",
                resource="auth",
                details=json.dumps({"email": user_info.email, "provider": provider_name}),
                ip_address=flask_request.remote_addr if flask_request else None,
            )
            self._db.audit_logs.create(audit.to_item())

            user_dict = user.to_api_dict()
            user_dict["isSuperAdmin"] = is_super_admin(user.id)
            user_dict["orgMemberships"] = get_user_org_memberships(user.id)

            return ResponseModel(
                success=True,
                data={
                    "user": user_dict,
                    "accessToken": id_token,
                    "refreshToken": refresh_token,
                    "token": id_token,
                    "oauthProvider": provider_name,
                },
                message="OAuth login successful",
            )
        except Exception as e:
            return ResponseModel(success=False, error=f"OAuth callback failed: {str(e)}", status_code=500)
