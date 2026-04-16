import json
from flask import request
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.user import UserItem
from database.schemas.audit_log import AuditLogItem
from utils import user_role_service


class UserResourceManager(IResourceManager):
    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action")

        if action == "list_users":
            return self._list_users(request_resource_model)
        elif action == "get_current_user":
            return self._get_current_user(request_resource_model)
        elif action == "list_my_orgs":
            return self._list_my_orgs(request_resource_model)

        return ResponseModel(success=False, error="Unknown action", status_code=400)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not supported", status_code=405)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action")

        if action == "update_role":
            return self._update_role(request_resource_model)
        elif action == "update_user":
            return self._update_user(request_resource_model)
        elif action == "update_preferences":
            return self._update_preferences(request_resource_model)

        return ResponseModel(success=False, error="Unknown action", status_code=400)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action")

        if action == "delete_user":
            return self._delete_user(request_resource_model)

        return ResponseModel(success=False, error="Unknown action", status_code=400)

    def _list_users(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = request_resource_model.user_id
        page = request_resource_model.data.get("page", 1)
        per_page = request_resource_model.data.get("per_page", 20)

        try:
            # Verify requesting user is super admin
            if not user_role_service.is_super_admin(str(user_id)):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            # Fetch all users and sort in memory for moderate user counts.
            all_items = self._db.users.list_all()

            # Sort by created_at descending
            all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            total = len(all_items)
            start = (page - 1) * per_page
            end = start + per_page
            page_items = all_items[start:end]

            users = [UserItem.from_item(item).to_api_dict() for item in page_items]

            return ResponseModel(
                success=True,
                data={
                    "users": users,
                    "total": total,
                    "page": page,
                    "perPage": per_page,
                },
            )
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get_current_user(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = request_resource_model.user_id

        try:
            item = self._db.users.get_by_id(str(user_id))
            if not item:
                return ResponseModel(success=False, error="User not found", status_code=404)

            user = UserItem.from_item(item)
            user_dict = user.to_api_dict()
            # Enrich with roles from user_roles table
            user_dict["isSuperAdmin"] = user_role_service.is_super_admin(user.id)
            user_dict["orgMemberships"] = user_role_service.get_user_org_memberships(user.id)
            return ResponseModel(success=True, data=user_dict)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_my_orgs(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        """List all organizations the current user belongs to."""
        user_id = str(request_resource_model.user_id)
        try:
            from database.schemas.organization import OrganizationItem
            org_ids = user_role_service.get_user_org_ids(user_id)
            if not org_ids:
                return ResponseModel(success=True, data={"organizations": []})

            org_items = self._db.organizations.batch_get_by_ids(org_ids)
            organizations = []
            for item in org_items:
                org = OrganizationItem.from_item(item)
                org_dict = org.to_api_dict()
                roles = user_role_service.get_user_org_roles(user_id, org.id)
                org_dict["userRoles"] = [r.role for r in roles]
                organizations.append(org_dict)

            return ResponseModel(success=True, data={"organizations": organizations})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_role(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = request_resource_model.user_id
        target_user_id = request_resource_model.data.get("target_user_id")
        new_role = request_resource_model.data.get("role")

        valid_roles = {"admin", "editor", "viewer", "owner", "manager", "member"}
        if new_role not in valid_roles:
            return ResponseModel(
                success=False,
                error=f"Invalid role. Must be one of: {', '.join(valid_roles)}",
                status_code=400,
            )

        try:
            # Verify requesting user is super admin
            if not user_role_service.is_super_admin(str(user_id)):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            # Get target user
            target_item = self._db.users.get_by_id(target_user_id)
            if not target_item:
                return ResponseModel(success=False, error="Target user not found", status_code=404)

            old_role = target_item.get("role", "viewer") if isinstance(target_item, dict) else getattr(target_item, "role", "viewer")
            target_org_id = target_item.get("org_id") if isinstance(target_item, dict) else getattr(target_item, "org_id", None)

            # Dual-write: update user record
            self._db.users.update_fields(target_user_id, {
                "role": new_role,
                "org_role": new_role,
                "updated_at": UserItem().updated_at,
            })

            # Write to user_roles table if user has an org
            if target_org_id:
                user_role_service.revoke_all_org_roles(target_user_id, target_org_id)
                user_role_service.grant_role(
                    user_id=target_user_id,
                    org_id=target_org_id,
                    role=new_role,
                    granted_by=str(user_id),
                )

            # Audit log
            audit = AuditLogItem(
                user_id=str(user_id),
                action="role_updated",
                resource="users",
                details=json.dumps({
                    "target_user_id": target_user_id,
                    "old_role": old_role,
                    "new_role": new_role,
                }),
                ip_address=request.remote_addr if hasattr(request, "remote_addr") else None,
            )
            self._db.audit_logs.create(audit.to_item())

            # Return updated user
            updated_item = self._db.users.get_by_id(target_user_id)
            updated_user = UserItem.from_item(updated_item)

            return ResponseModel(
                success=True,
                data=updated_user.to_api_dict(),
                message=f"Role updated to {new_role}",
            )
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_preferences(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = str(request_resource_model.user_id)
        data = request_resource_model.data

        try:
            user_item = self._db.users.get_by_id(user_id)
            if not user_item:
                return ResponseModel(success=False, error="User not found", status_code=404)

            updates = {}
            if "timezone" in data:
                updates["timezone"] = data["timezone"]
            if "weeklyCapacity" in data:
                updates["weekly_capacity"] = int(data["weeklyCapacity"])
            if "defaultHourlyRate" in data:
                updates["default_hourly_rate"] = str(data["defaultHourlyRate"]) if data["defaultHourlyRate"] else None
            if "notificationPreferences" in data:
                notif = data["notificationPreferences"]
                updates["notification_preferences"] = json.dumps(notif) if isinstance(notif, dict) else notif

            if not updates:
                return ResponseModel(success=False, error="No updatable fields provided", status_code=400)

            updates["updated_at"] = UserItem().updated_at
            self._db.users.update_fields(user_id, updates)

            updated_item = self._db.users.get_by_id(user_id)
            updated_user = UserItem.from_item(updated_item)
            return ResponseModel(success=True, data=updated_user.to_api_dict(), message="Preferences updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_user(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = request_resource_model.user_id
        target_user_id = request_resource_model.data.get("target_user_id")
        data = request_resource_model.data

        try:
            # Users can update themselves; admins can update anyone
            requesting_user = self._db.users.get_by_id(str(user_id))
            if not requesting_user:
                return ResponseModel(success=False, error="User not found", status_code=404)

            if str(user_id) != target_user_id and not user_role_service.is_super_admin(str(user_id)):
                return ResponseModel(success=False, error="Not authorized", status_code=403)

            # Verify target user exists
            target_item = self._db.users.get_by_id(target_user_id)
            if not target_item:
                return ResponseModel(success=False, error="Target user not found", status_code=404)

            # Build update fields for allowed fields
            updatable_fields = {
                "firstName": "first_name",
                "lastName": "last_name",
                "username": "username",
                "organizationId": "organization_id",
                "phone": "phone",
                "avatarUrl": "avatar_url",
            }

            updates = {}
            for api_key, db_key in updatable_fields.items():
                if api_key in data:
                    updates[db_key] = data[api_key]

            if not updates:
                return ResponseModel(success=False, error="No updatable fields provided", status_code=400)

            updates["updated_at"] = UserItem().updated_at
            self._db.users.update_fields(target_user_id, updates)

            # Return updated user
            updated_item = self._db.users.get_by_id(target_user_id)
            updated_user = UserItem.from_item(updated_item)

            return ResponseModel(success=True, data=updated_user.to_api_dict(), message="User updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _delete_user(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = request_resource_model.user_id
        target_user_id = request_resource_model.data.get("target_user_id")

        try:
            # Verify requesting user is super admin
            if not user_role_service.is_super_admin(str(user_id)):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            if str(user_id) == target_user_id:
                return ResponseModel(success=False, error="Cannot delete your own account", status_code=400)

            target_item = self._db.users.get_by_id(target_user_id)
            if not target_item:
                return ResponseModel(success=False, error="User not found", status_code=404)

            target_email = target_item.get("email", "") if isinstance(target_item, dict) else getattr(target_item, "email", "")

            # Audit log before deletion
            audit = AuditLogItem(
                user_id=str(user_id),
                action="user_deleted",
                resource="users",
                details=json.dumps({
                    "deleted_user_id": target_user_id,
                    "deleted_email": target_email,
                }),
                ip_address=request.remote_addr if hasattr(request, "remote_addr") else None,
            )
            self._db.audit_logs.create(audit.to_item())

            # Delete the user
            self._db.users.delete(target_user_id)

            return ResponseModel(success=True, message="User deleted successfully")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
