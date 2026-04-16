"""Project Resource Manager - AI project CRUD."""
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.project import ProjectItem


class ProjectResourceManager(IResourceManager):

    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "list":
            return self._list(req)
        elif action == "get":
            return self._get(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "create":
            return self._create(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def put(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "update":
            return self._update(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def delete(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "delete":
            return self._delete(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def _get_org_id(self, user_id):
        user = self._db.users.get_by_id(str(user_id))
        return user.org_id if user else None

    def _list(self, req):
        try:
            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)
            items = self._db.projects.list_all(org_id=org_id)
            projects = [ProjectItem.from_item(i).to_api_dict() for i in items]
            status = req.data.get("status")
            if status:
                projects = [p for p in projects if p["status"] == status]
            return ResponseModel(success=True, data={"projects": projects})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get(self, req):
        try:
            org_id = self._get_org_id(req.user_id)
            project_id = req.data.get("project_id")
            item = self._db.projects.get_by_key({"org_id": org_id, "id": project_id})
            if not item:
                return ResponseModel(success=False, error="Project not found", status_code=404)
            return ResponseModel(success=True, data={"project": ProjectItem.from_item(item).to_api_dict()})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _create(self, req):
        try:
            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)
            project = ProjectItem(
                org_id=org_id,
                name=req.data.get("name", ""),
                project_type=req.data.get("projectType", "ai_report"),
                description=req.data.get("description"),
            )
            self._db.projects.create(project.to_item())
            return ResponseModel(success=True, data={"project": project.to_api_dict()}, status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update(self, req):
        try:
            org_id = self._get_org_id(req.user_id)
            project_id = req.data.get("project_id")
            updates = {}
            for field, api_field in [("name", "name"), ("description", "description"),
                                      ("status", "status"), ("project_type", "projectType")]:
                if api_field in req.data:
                    updates[field] = req.data[api_field]
            if not updates:
                return ResponseModel(success=False, error="No fields to update", status_code=400)
            updates["updated_at"] = datetime.utcnow().isoformat()
            expr_parts, values, names = [], {}, {}
            for i, (k, v) in enumerate(updates.items()):
                attr = f"#a{i}" if k in ("name", "status") else k
                if k in ("name", "status"):
                    names[attr] = k
                expr_parts.append(f"{attr} = :v{i}")
                values[f":v{i}"] = v
            kwargs = {"Key": {"org_id": org_id, "id": project_id},
                      "UpdateExpression": "SET " + ", ".join(expr_parts),
                      "ExpressionAttributeValues": values}
            if names:
                kwargs["ExpressionAttributeNames"] = names
            self._db.projects.raw_update_item(**kwargs)
            return ResponseModel(success=True, message="Project updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _delete(self, req):
        try:
            org_id = self._get_org_id(req.user_id)
            project_id = req.data.get("project_id")
            self._db.projects.delete_by_key({"org_id": org_id, "id": project_id})
            return ResponseModel(success=True, message="Project deleted")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
