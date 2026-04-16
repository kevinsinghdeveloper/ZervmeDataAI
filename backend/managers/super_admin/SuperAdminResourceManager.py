"""Super Admin Resource Manager."""
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.organization import OrganizationItem
from database.schemas.user import UserItem
from utils import user_role_service

COGNITO_REGION = os.getenv("AWS_REGION_NAME", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")


class SuperAdminResourceManager(IResourceManager):
    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "list_organizations":
            return self._list_orgs(req)
        elif action == "list_users":
            return self._list_users(req)
        elif action == "stats":
            return self._stats(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "grant_super_admin":
            return self._grant_super_admin(req)
        elif action == "reset_password":
            return self._reset_password(req)
        return ResponseModel(success=False, error="Not implemented", status_code=405)

    def put(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "update_organization":
            return self._update_org(req)
        elif action == "toggle_user":
            return self._toggle_user(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def delete(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "revoke_super_admin":
            return self._revoke_super_admin(req)
        return ResponseModel(success=False, error="Not implemented", status_code=405)

    def _list_orgs(self, req):
        try:
            items = self._db.organizations.list_all()
            orgs = [OrganizationItem.from_item(i).to_api_dict() for i in items]
            return ResponseModel(success=True, data={"organizations": orgs, "total": len(orgs)})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_users(self, req):
        try:
            items = self._db.users.list_all()
            users = []
            for i in items:
                user = UserItem.from_item(i)
                user_dict = user.to_api_dict()
                user_dict["isSuperAdmin"] = user_role_service.is_super_admin(user.id)
                user_dict["orgMemberships"] = user_role_service.get_user_org_memberships(user.id)
                users.append(user_dict)
            return ResponseModel(success=True, data={"users": users, "total": len(users)})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _stats(self, req):
        try:
            from datetime import datetime, timezone
            orgs = self._db.organizations.count()
            users = self._db.users.count()
            active_users = self._db.users.count(is_active=True)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            try:
                today_entries = self._db.time_entries.count(date=today)
            except Exception:
                today_entries = 0
            return ResponseModel(success=True, data={
                "totalOrganizations": orgs,
                "totalUsers": users,
                "activeUsers": active_users,
                "entriesToday": today_entries,
            })
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_org(self, req):
        try:
            org_id = req.data.get("org_id")
            updates = {}
            for f in ["is_active", "plan_tier"]:
                camel = {"is_active": "isActive", "plan_tier": "planTier"}.get(f, f)
                if camel in req.data:
                    updates[f] = req.data[camel]
            if not updates:
                return ResponseModel(success=False, error="No fields", status_code=400)
            updates["updated_at"] = datetime.utcnow().isoformat()
            self._db.organizations.update(org_id, updates)
            return ResponseModel(success=True, message="Organization updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _toggle_user(self, req):
        try:
            target = req.data.get("target_user_id")
            user = self._db.users.get_by_id(target)
            current_active = user.is_active if user else True
            new_active = not current_active
            self._db.users.update_fields(target, {
                "is_active": new_active,
                "updated_at": datetime.utcnow().isoformat(),
            })
            return ResponseModel(success=True, message=f"User {'activated' if new_active else 'deactivated'}")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _reset_password(self, req):
        """Admin reset password for any user via Cognito admin API."""
        try:
            target_user_id = req.data.get("target_user_id")
            new_password = req.data.get("newPassword", "")

            if not target_user_id or not new_password:
                return ResponseModel(success=False, error="target_user_id and newPassword are required", status_code=400)

            if len(new_password) < 8:
                return ResponseModel(success=False, error="Password must be at least 8 characters", status_code=400)

            # Look up user to get their email (Cognito username)
            user = self._db.users.get_by_id(target_user_id)
            if not user:
                return ResponseModel(success=False, error="User not found", status_code=404)

            email = user.get("email", "") if isinstance(user, dict) else getattr(user, "email", "")
            if not email:
                return ResponseModel(success=False, error="User has no email", status_code=400)

            cognito = boto3.client("cognito-idp", region_name=COGNITO_REGION)
            cognito.admin_set_user_password(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=email,
                Password=new_password,
                Permanent=True,
            )

            return ResponseModel(success=True, message=f"Password reset for {email}")
        except ClientError as e:
            return ResponseModel(success=False, error=str(e.response["Error"]["Message"]), status_code=400)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _grant_super_admin(self, req):
        """Grant super_admin role to a user."""
        try:
            target_user_id = req.data.get("target_user_id")
            if not target_user_id:
                return ResponseModel(success=False, error="target_user_id is required", status_code=400)

            user_role_service.grant_role(
                user_id=target_user_id,
                org_id="GLOBAL",
                role="super_admin",
                granted_by=str(req.user_id),
            )

            # Dual-write: update user record
            self._db.users.update_fields(target_user_id, {
                "is_super_admin": True,
                "updated_at": datetime.utcnow().isoformat(),
            })

            return ResponseModel(success=True, message="Super admin granted")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _revoke_super_admin(self, req):
        """Revoke super_admin role from a user."""
        try:
            target_user_id = req.data.get("target_user_id")
            if not target_user_id:
                return ResponseModel(success=False, error="target_user_id is required", status_code=400)

            # Don't allow revoking your own super admin
            if str(req.user_id) == target_user_id:
                return ResponseModel(success=False, error="Cannot revoke your own super admin", status_code=400)

            user_role_service.revoke_role(target_user_id, "GLOBAL", "super_admin")

            # Dual-write: update user record
            self._db.users.update_fields(target_user_id, {
                "is_super_admin": False,
                "updated_at": datetime.utcnow().isoformat(),
            })

            return ResponseModel(success=True, message="Super admin revoked")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
