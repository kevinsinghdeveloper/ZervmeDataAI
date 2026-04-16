import os
import boto3
from botocore.exceptions import ClientError
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.user import UserItem

COGNITO_REGION = os.getenv("AWS_REGION_NAME", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")

# Default theme configuration (consulting template pattern)
DEFAULT_THEME = {
    "primaryColor": "#1976d2",
    "secondaryColor": "#dc004e",
    "backgroundColor": "#0f172a",
    "paperColor": "#1e293b",
    "textColor": "#333333",
    "logoUrl": "",
    "faviconUrl": "",
    "appName": "Zerve Direct",
    "fontFamily": "Inter, system-ui, sans-serif",
}

DEFAULT_SETTINGS = {
    "allowPublicChat": True,
    "requireEmailVerification": False,
    "maxUploadSizeMb": 50,
    "defaultModel": "claude-sonnet-4-5-20250929",
    "enableAuditLogging": True,
    "chatbotSystemPrompt": "You are a time tracking assistant for Zerve My Time. Help users analyze their time data, suggest improvements, and answer questions about their tracked hours, projects, and team utilization.",
    "maxConversationHistory": 10,
}


class ConfigResourceManager(IResourceManager):
    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action")

        if action == "get_theme":
            return self._get_theme(request_resource_model)

        if action == "get_settings":
            return self._get_settings(request_resource_model)

        return ResponseModel(success=False, error="Unknown action", status_code=400)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action")

        if action == "update_theme":
            return self._update_theme(request_resource_model)

        if action == "update_settings":
            return self._update_settings(request_resource_model)

        if action == "upload_asset":
            return self._upload_asset(request_resource_model)

        if action == "first_user":
            return self._create_first_user(request_resource_model.data)

        return ResponseModel(success=False, error="Unknown action", status_code=400)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not supported", status_code=405)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not supported", status_code=405)

    def _get_theme(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            item = self._db.config.get_config("CONFIG", "theme")

            if item:
                # Remove DynamoDB keys from the response
                theme = {k: v for k, v in item.items() if k not in ("pk", "sk")}
            else:
                theme = dict(DEFAULT_THEME)

            # Generate fresh presigned URLs from stored S3 keys
            bucket = os.getenv("UPLOADS_BUCKET", "")
            if bucket:
                s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION_NAME", "us-east-1"))
                for s3_key_field, url_field in [("logoS3Key", "logoUrl"), ("faviconS3Key", "faviconUrl")]:
                    s3_key = theme.get(s3_key_field)
                    if s3_key:
                        theme[url_field] = s3_client.generate_presigned_url(
                            "get_object",
                            Params={"Bucket": bucket, "Key": s3_key},
                            ExpiresIn=604800,  # 7 days
                        )

            return ResponseModel(success=True, data=theme)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_theme(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        data = request_resource_model.data

        try:
            # Verify the user is an admin
            user_item = self._db.users.get_by_id(str(request_resource_model.user_id))
            if not user_item or not getattr(user_item, "is_super_admin", False):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            # Get current theme or use defaults
            existing = self._db.config.get_config("CONFIG", "theme")

            if existing:
                theme = {k: v for k, v in existing.items() if k not in ("pk", "sk")}
            else:
                theme = dict(DEFAULT_THEME)

            # Normalize nested frontend format to flat backend format
            colors = data.get("colors")
            if isinstance(colors, dict):
                if "primary" in colors:
                    data["primaryColor"] = colors["primary"]
                if "secondary" in colors:
                    data["secondaryColor"] = colors["secondary"]
                if "tertiary" in colors:
                    data["tertiaryColor"] = colors["tertiary"]
                if "background" in colors:
                    data["backgroundColor"] = colors["background"]
                if "paper" in colors:
                    data["paperColor"] = colors["paper"]
            if "logo" in data:
                data["logoUrl"] = data["logo"] or ""
            if "favicon" in data:
                data["faviconUrl"] = data["favicon"] or ""

            # Apply allowed updates
            allowed_keys = {
                "primaryColor", "secondaryColor", "tertiaryColor",
                "backgroundColor", "paperColor", "textColor",
                "logoUrl", "faviconUrl", "appName", "fontFamily",
            }
            for key in allowed_keys:
                if key in data:
                    theme[key] = data[key]

            # Save to DynamoDB
            self._db.config.put_config("CONFIG", "theme", theme)

            return ResponseModel(success=True, data=theme, message="Theme updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _upload_asset(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        data = request_resource_model.data

        try:
            # Verify the user is an admin
            user_item = self._db.users.get_by_id(str(request_resource_model.user_id))
            if not user_item or not getattr(user_item, "is_super_admin", False):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            file_content = data.get("file_content")
            file_name = data.get("file_name", "")
            asset_type = data.get("asset_type", "")
            content_type = data.get("content_type", "application/octet-stream")

            if not file_content or not asset_type:
                return ResponseModel(success=False, error="File and asset type are required", status_code=400)

            if asset_type not in ("logo", "favicon"):
                return ResponseModel(success=False, error="Asset type must be 'logo' or 'favicon'", status_code=400)

            # Validate file extension
            allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp"}
            ext = os.path.splitext(file_name)[1].lower()
            if ext not in allowed_extensions:
                return ResponseModel(
                    success=False,
                    error=f"Invalid file type. Allowed: {', '.join(sorted(allowed_extensions))}",
                    status_code=400,
                )

            # Validate file size (max 2MB)
            max_size = 2 * 1024 * 1024
            if len(file_content) > max_size:
                return ResponseModel(success=False, error="File size exceeds 2MB limit", status_code=400)

            # Upload to storage
            storage = self._service_managers.get("storage")
            if not storage:
                return ResponseModel(success=False, error="Storage service unavailable", status_code=500)

            key = f"config/{asset_type}{ext}"
            storage.upload_file(key, file_content, content_type)

            # Store the S3 key (not a URL) in DynamoDB so we can generate fresh presigned URLs
            existing = self._db.config.get_config("CONFIG", "theme")
            if existing:
                theme = {k: v for k, v in existing.items() if k not in ("pk", "sk")}
            else:
                theme = dict(DEFAULT_THEME)

            s3_key_field = "logoS3Key" if asset_type == "logo" else "faviconS3Key"
            theme[s3_key_field] = key

            # Also generate a presigned URL for immediate use
            bucket = os.getenv("UPLOADS_BUCKET", "")
            s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION_NAME", "us-east-1"))
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=604800,  # 7 days
            )

            url_key = "logoUrl" if asset_type == "logo" else "faviconUrl"
            theme[url_key] = url

            self._db.config.put_config("CONFIG", "theme", theme)

            return ResponseModel(success=True, data={"url": url, "assetType": asset_type})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get_settings(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        try:
            item = self._db.config.get_config("CONFIG", "settings")

            if item:
                settings = {k: v for k, v in item.items() if k not in ("pk", "sk")}
            else:
                settings = dict(DEFAULT_SETTINGS)

            return ResponseModel(success=True, data=settings)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_settings(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        data = request_resource_model.data

        try:
            # Verify the user is an admin
            user_item = self._db.users.get_by_id(str(request_resource_model.user_id))
            if not user_item or not getattr(user_item, "is_super_admin", False):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            # Get current settings or use defaults
            existing = self._db.config.get_config("CONFIG", "settings")

            if existing:
                settings = {k: v for k, v in existing.items() if k not in ("pk", "sk")}
            else:
                settings = dict(DEFAULT_SETTINGS)

            # Apply allowed updates
            allowed_keys = {
                "allowPublicChat", "requireEmailVerification",
                "maxUploadSizeMb", "defaultModel", "enableAuditLogging",
                "maintenanceMode", "defaultUserRole",
                "jwtExpiryHours", "maxLoginAttempts", "lockoutDurationMinutes",
                "enableRateLimiting", "enableTwoFactor", "corsOrigins",
                "chatbotSystemPrompt", "maxConversationHistory",
            }
            for key in allowed_keys:
                if key in data:
                    settings[key] = data[key]

            # Save to DynamoDB
            self._db.config.put_config("CONFIG", "settings", settings)

            return ResponseModel(success=True, data=settings, message="Settings updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _create_first_user(self, data: dict) -> ResponseModel:
        """Create the first admin user during initial setup via Cognito."""
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")

        if not email or not password:
            return ResponseModel(success=False, error="Email and password are required", status_code=400)

        try:
            # Check if any users exist
            if self._db.users.scan_count() > 0:
                return ResponseModel(
                    success=False,
                    error="First user already created. Use regular registration.",
                    status_code=409,
                )

            # Create user in Cognito
            cognito = boto3.client("cognito-idp", region_name=COGNITO_REGION)
            try:
                signup_resp = cognito.sign_up(
                    ClientId=COGNITO_CLIENT_ID,
                    Username=email,
                    Password=password,
                    UserAttributes=[
                        {"Name": "email", "Value": email},
                        {"Name": "given_name", "Value": first_name},
                        {"Name": "family_name", "Value": last_name},
                    ],
                )
                cognito_sub = signup_resp["UserSub"]

                # Auto-confirm the first user
                cognito.admin_confirm_sign_up(
                    UserPoolId=COGNITO_USER_POOL_ID,
                    Username=email,
                )
            except ClientError as e:
                return ResponseModel(
                    success=False,
                    error=str(e.response["Error"]["Message"]),
                    status_code=400,
                )

            # Create admin user profile in DynamoDB
            user = UserItem(
                id=cognito_sub,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role="admin",
                is_super_admin=True,
                is_verified=True,
                is_active=True,
            )
            self._db.users.create(user)

            # Log the user in to get tokens
            try:
                auth_resp = cognito.initiate_auth(
                    ClientId=COGNITO_CLIENT_ID,
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters={"USERNAME": email, "PASSWORD": password},
                )
                tokens = auth_resp.get("AuthenticationResult", {})
            except ClientError:
                tokens = {}

            return ResponseModel(
                success=True,
                data={
                    "user": user.to_api_dict(),
                    "token": tokens.get("IdToken", ""),
                    "accessToken": tokens.get("IdToken", ""),
                    "refreshToken": tokens.get("RefreshToken", ""),
                },
                message="First admin user created",
                status_code=201,
            )
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
