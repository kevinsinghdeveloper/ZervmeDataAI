"""Report Resource Manager - report CRUD operations."""
import json
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.report import ReportItem


class ReportResourceManager(IResourceManager):

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

    def _list(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)
            items = self._db.reports.list_all(org_id=org_id)
            reports = [ReportItem.from_item(i).to_api_dict() for i in items]
            project_id = req.data.get("project_id")
            if project_id:
                reports = [r for r in reports if r["projectId"] == project_id]
            return ResponseModel(success=True, data={"reports": reports})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            report_id = req.data.get("report_id")
            item = self._db.reports.get_by_key({"org_id": org_id, "id": report_id})
            if not item:
                return ResponseModel(success=False, error="Report not found", status_code=404)
            return ResponseModel(success=True, data={"report": ReportItem.from_item(item).to_api_dict()})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _create(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)
            dataset_config = req.data.get("datasetConfig")
            if dataset_config and not isinstance(dataset_config, str):
                dataset_config = json.dumps(dataset_config)
            report_config = req.data.get("reportConfig")
            if report_config and not isinstance(report_config, str):
                report_config = json.dumps(report_config)
            report = ReportItem(
                org_id=org_id,
                name=req.data.get("name", ""),
                project_id=req.data.get("projectId"),
                report_type_id=req.data.get("reportTypeId"),
                model_id=req.data.get("modelId"),
                dataset_config=dataset_config,
                report_config=report_config,
            )
            self._db.reports.create(report.to_item())
            return ResponseModel(success=True, data={"report": report.to_api_dict()}, status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            report_id = req.data.get("report_id")
            updates = {}
            for field, api_field in [("name", "name"), ("project_id", "projectId"),
                                      ("report_type_id", "reportTypeId"),
                                      ("model_id", "modelId"), ("status", "status")]:
                if api_field in req.data:
                    updates[field] = req.data[api_field]
            for json_field, api_field in [("dataset_config", "datasetConfig"),
                                           ("report_config", "reportConfig")]:
                if api_field in req.data:
                    val = req.data[api_field]
                    updates[json_field] = json.dumps(val) if not isinstance(val, str) else val
            if not updates:
                return ResponseModel(success=False, error="No fields to update", status_code=400)
            updates["updated_at"] = datetime.utcnow().isoformat()
            # DynamoDB reserved words: name, status
            reserved = {"name", "status"}
            expr_parts, values, names = [], {}, {}
            for i, (k, v) in enumerate(updates.items()):
                attr = f"#a{i}" if k in reserved else k
                if k in reserved:
                    names[attr] = k
                expr_parts.append(f"{attr} = :v{i}")
                values[f":v{i}"] = v
            kwargs = {
                "Key": {"org_id": org_id, "id": report_id},
                "UpdateExpression": "SET " + ", ".join(expr_parts),
                "ExpressionAttributeValues": values,
            }
            if names:
                kwargs["ExpressionAttributeNames"] = names
            self._db.reports.raw_update_item(**kwargs)
            return ResponseModel(success=True, message="Report updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _delete(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            report_id = req.data.get("report_id")
            self._db.reports.delete_by_key({"org_id": org_id, "id": report_id})
            return ResponseModel(success=True, message="Report deleted")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
