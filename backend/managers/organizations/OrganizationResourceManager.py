"""Organization Resource Manager - org CRUD, invitations, members."""
import json
import re
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.organization import OrganizationItem
from database.schemas.org_invitation import OrgInvitationItem
from database.schemas.user import UserItem
from database.schemas.audit_log import AuditLogItem
from utils import user_role_service


class OrganizationResourceManager(IResourceManager):

    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "get_current":
            return self._get_current(req)
        elif action == "list_invitations":
            return self._list_invitations(req)
        elif action == "list_members":
            return self._list_members(req)
        elif action == "list_member_roles":
            return self._list_member_roles(req)
        elif action == "list_my_orgs":
            return self._list_my_orgs(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "create":
            return self._create(req)
        elif action == "create_invitation":
            return self._create_invitation(req)
        elif action == "add_member_role":
            return self._add_member_role(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def put(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "update_current":
            return self._update_current(req)
        elif action == "update_member_role":
            return self._update_member_role(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def delete(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "delete_invitation":
            return self._delete_invitation(req)
        elif action == "remove_member":
            return self._remove_member(req)
        elif action == "remove_member_role":
            return self._remove_member_role(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def _get_org_id(self, req):
        """Get org_id from X-Org-Id header or user's inline org_id (backward compat)."""
        from flask import request as flask_request
        org_id = flask_request.headers.get("X-Org-Id")
        if org_id:
            return org_id
        user = self._get_user(req.user_id)
        return user.org_id if user else None

    def _get_current(self, req):
        try:
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization found", status_code=404)
            item = self._db.organizations.raw_get_item({"id": org_id})
            if not item:
                return ResponseModel(success=False, error="Organization not found", status_code=404)
            org = OrganizationItem.from_item(item)
            return ResponseModel(success=True, data={"organization": org.to_api_dict()})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _create(self, req):
        try:
            name = req.data.get("name", "").strip()
            if not name:
                return ResponseModel(success=False, error="Organization name is required", status_code=400)
            slug = re.sub(r'[^a-z0-9-]', '', name.lower().replace(' ', '-'))
            org = OrganizationItem(name=name, slug=slug, owner_id=str(req.user_id), member_count=1)
            self._db.organizations.create(org.to_item())

            # Dual-write: update user record (backward compat)
            self._db.users.raw_update_item(
                Key={"id": str(req.user_id)},
                UpdateExpression="SET org_id = :o, org_role = :r, updated_at = :u",
                ExpressionAttributeValues={":o": org.id, ":r": "owner", ":u": datetime.utcnow().isoformat()},
            )
            # Write to user_roles table
            user_role_service.grant_role(
                user_id=str(req.user_id),
                org_id=org.id,
                role="owner",
                granted_by=str(req.user_id),
            )

            return ResponseModel(success=True, data={"organization": org.to_api_dict()}, message="Organization created", status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_current(self, req):
        try:
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization found", status_code=404)
            updates = {}
            for field in ["name", "settings"]:
                if field in req.data:
                    val = req.data[field]
                    if field == "settings" and isinstance(val, dict):
                        val = json.dumps(val)
                    updates[field] = val
            if not updates:
                return ResponseModel(success=False, error="No fields to update", status_code=400)
            expr_parts, values = [], {}
            for i, (k, v) in enumerate(updates.items()):
                expr_parts.append(f"#{k} = :v{i}")
                values[f":v{i}"] = v
            expr_parts.append("updated_at = :upd")
            values[":upd"] = datetime.utcnow().isoformat()
            names = {f"#{k}": k for k in updates}
            self._db.organizations.raw_update_item(
                Key={"id": org_id},
                UpdateExpression="SET " + ", ".join(expr_parts),
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
            )
            return ResponseModel(success=True, message="Organization updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_invitations(self, req):
        try:
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)
            from boto3.dynamodb.conditions import Key
            resp = self._db.org_invitations.raw_query(
                IndexName="OrgIdIndex",
                KeyConditionExpression=Key("org_id").eq(org_id),
            )
            items = [OrgInvitationItem.from_item(i).to_api_dict() for i in resp.get("Items", [])]
            return ResponseModel(success=True, data={"invitations": items})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _create_invitation(self, req):
        try:
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)
            email = req.data.get("email", "").strip().lower()
            role = req.data.get("role", "member")
            if not email:
                return ResponseModel(success=False, error="Email is required", status_code=400)

            # Validate role is a valid org role
            valid_roles = {"member", "manager", "admin", "owner"}
            if role not in valid_roles:
                return ResponseModel(success=False, error=f"Invalid role. Must be one of: {', '.join(valid_roles)}", status_code=400)

            invite = OrgInvitationItem(org_id=org_id, email=email, role=role, invited_by=str(req.user_id))
            self._db.org_invitations.create(invite.to_item())
            email_service = self._service_managers.get("email")
            if email_service:
                try:
                    result = email_service.send_org_invitation(email, org_id, invite.token)
                    print(f"Org invitation email to {email}: {'sent' if result else 'failed'}")
                except Exception as e:
                    print(f"Org invitation email error: {e}")
            return ResponseModel(success=True, data={"invitation": invite.to_api_dict()}, message="Invitation sent", status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _delete_invitation(self, req):
        try:
            invitation_id = req.data.get("invitation_id")
            self._db.org_invitations.delete(invitation_id)
            return ResponseModel(success=True, message="Invitation deleted")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_members(self, req):
        """List org members by querying user_roles table, then fetching user profiles."""
        try:
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            # Get all role entries for this org from user_roles table
            role_entries = user_role_service.get_org_members(org_id)

            # Group roles by user_id
            user_roles_map = {}
            for entry in role_entries:
                if entry.user_id not in user_roles_map:
                    user_roles_map[entry.user_id] = []
                user_roles_map[entry.user_id].append(entry.role)

            if not user_roles_map:
                # Fallback: try legacy query via users table OrgIdIndex
                from boto3.dynamodb.conditions import Key, Attr
                try:
                    resp = self._db.users.raw_query(
                        IndexName="OrgIdIndex",
                        KeyConditionExpression=Key("org_id").eq(org_id),
                    )
                except Exception:
                    resp = self._db.users.raw_scan(FilterExpression=Attr("org_id").eq(org_id))
                members = [UserItem.from_item(i).to_api_dict() for i in resp.get("Items", [])]
                return ResponseModel(success=True, data={"members": members})

            # Batch get user profiles
            user_ids = list(user_roles_map.keys())
            members = []

            # DynamoDB BatchGetItem supports max 100 keys per call
            for i in range(0, len(user_ids), 100):
                batch = user_ids[i:i + 100]
                user_items = self._db.users.batch_get_by_ids(batch)
                for item in user_items:
                    user = UserItem.from_item(item)
                    user_dict = user.to_api_dict()
                    # Add roles array from user_roles table
                    user_dict["orgRoles"] = user_roles_map.get(user.id, [])
                    # Set orgRole to highest role for backward compat
                    roles = user_roles_map.get(user.id, [])
                    hierarchy = user_role_service.ORG_ROLE_HIERARCHY
                    if roles:
                        highest = max(roles, key=lambda r: hierarchy.index(r) if r in hierarchy else -1)
                        user_dict["orgRole"] = highest
                    members.append(user_dict)

            return ResponseModel(success=True, data={"members": members})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update_member_role(self, req):
        """Backward-compat: set a single role (replaces all existing org roles)."""
        try:
            member_id = req.data.get("member_id")
            new_role = req.data.get("role", "member")
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            # Revoke all existing org roles and grant the new one
            user_role_service.revoke_all_org_roles(member_id, org_id)
            user_role_service.grant_role(
                user_id=member_id, org_id=org_id, role=new_role,
                granted_by=str(req.user_id),
            )

            # Dual-write: update user record
            self._db.users.raw_update_item(
                Key={"id": member_id},
                UpdateExpression="SET org_role = :r, #rl = :r, updated_at = :u",
                ExpressionAttributeNames={"#rl": "role"},
                ExpressionAttributeValues={":r": new_role, ":u": datetime.utcnow().isoformat()},
            )
            return ResponseModel(success=True, message="Role updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _add_member_role(self, req):
        """Add a role to a member (multi-role support)."""
        try:
            member_id = req.data.get("member_id")
            role = req.data.get("role", "member")
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            valid_roles = {"member", "manager", "admin", "owner"}
            if role not in valid_roles:
                return ResponseModel(success=False, error=f"Invalid role. Must be one of: {', '.join(valid_roles)}", status_code=400)

            user_role_service.grant_role(
                user_id=member_id, org_id=org_id, role=role,
                granted_by=str(req.user_id),
            )
            return ResponseModel(success=True, message=f"Role '{role}' granted")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _remove_member_role(self, req):
        """Remove a specific role from a member."""
        try:
            member_id = req.data.get("member_id")
            role = req.data.get("role")
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            # Protect against removing the last owner
            if role == "owner" and user_role_service.is_last_owner(org_id):
                return ResponseModel(success=False, error="Cannot remove the last owner", status_code=400)

            user_role_service.revoke_role(member_id, org_id, role)
            return ResponseModel(success=True, message=f"Role '{role}' revoked")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_member_roles(self, req):
        """List all roles for a specific member in the org."""
        try:
            member_id = req.data.get("member_id")
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            roles = user_role_service.get_user_org_roles(member_id, org_id)
            return ResponseModel(success=True, data={
                "roles": [r.to_api_dict() for r in roles]
            })
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _list_my_orgs(self, req):
        """List all organizations the current user belongs to."""
        try:
            user_id = str(req.user_id)
            org_ids = user_role_service.get_user_org_ids(user_id)

            if not org_ids:
                return ResponseModel(success=True, data={"organizations": []})

            # Batch get org details
            organizations = []
            for i in range(0, len(org_ids), 100):
                batch = org_ids[i:i + 100]
                org_items = self._db.organizations.batch_get_by_ids(batch)
                for item in org_items:
                    org = OrganizationItem.from_item(item)
                    org_dict = org.to_api_dict()
                    # Include user's roles in this org
                    roles = user_role_service.get_user_org_roles(user_id, org.id)
                    org_dict["userRoles"] = [r.role for r in roles]
                    organizations.append(org_dict)

            return ResponseModel(success=True, data={"organizations": organizations})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _remove_member(self, req):
        try:
            member_id = req.data.get("member_id")
            org_id = self._get_org_id(req)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)

            # Revoke all roles in user_roles table
            user_role_service.revoke_all_org_roles(member_id, org_id)

            # Dual-write: remove from user record (backward compat)
            self._db.users.raw_update_item(
                Key={"id": member_id},
                UpdateExpression="REMOVE org_id, org_role SET updated_at = :u",
                ExpressionAttributeValues={":u": datetime.utcnow().isoformat()},
            )

            # Decrement org member_count
            self._db.organizations.raw_update_item(
                Key={"id": org_id},
                UpdateExpression="SET member_count = if_not_exists(member_count, :one) - :dec, updated_at = :u",
                ExpressionAttributeValues={
                    ":dec": 1,
                    ":one": 1,
                    ":u": datetime.utcnow().isoformat(),
                },
            )

            return ResponseModel(success=True, message="Member removed")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get_user(self, user_id):
        user = self._db.users.get_by_id(str(user_id))
        return user
