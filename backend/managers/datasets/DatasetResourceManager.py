"""Dataset Resource Manager - dataset CRUD operations."""
import json
from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.dataset import DatasetItem


class DatasetResourceManager(IResourceManager):

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
            items = self._db.datasets.list_all(org_id=org_id)
            datasets = [DatasetItem.from_item(i).to_api_dict() for i in items]
            status = req.data.get("status")
            if status:
                datasets = [d for d in datasets if d["status"] == status]
            return ResponseModel(success=True, data={"datasets": datasets})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            dataset_id = req.data.get("dataset_id")
            item = self._db.datasets.get_by_key({"org_id": org_id, "id": dataset_id})
            if not item:
                return ResponseModel(success=False, error="Dataset not found", status_code=404)
            return ResponseModel(success=True, data={"dataset": DatasetItem.from_item(item).to_api_dict()})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _create(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            if not org_id:
                return ResponseModel(success=False, error="No organization", status_code=404)
            domain_data = req.data.get("domainData")
            if domain_data and not isinstance(domain_data, str):
                domain_data = json.dumps(domain_data)
            dataset = DatasetItem(
                org_id=org_id,
                name=req.data.get("name", ""),
                description=req.data.get("description"),
                domain_data=domain_data,
                data_source=req.data.get("dataSource"),
            )
            self._db.datasets.create(dataset.to_item())
            return ResponseModel(success=True, data={"dataset": dataset.to_api_dict()}, status_code=201)
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _update(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            dataset_id = req.data.get("dataset_id")
            updates = {}
            for field, api_field in [("name", "name"), ("description", "description"),
                                      ("data_source", "dataSource"), ("status", "status")]:
                if api_field in req.data:
                    updates[field] = req.data[api_field]
            if "domainData" in req.data:
                val = req.data["domainData"]
                updates["domain_data"] = json.dumps(val) if not isinstance(val, str) else val
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
                "Key": {"org_id": org_id, "id": dataset_id},
                "UpdateExpression": "SET " + ", ".join(expr_parts),
                "ExpressionAttributeValues": values,
            }
            if names:
                kwargs["ExpressionAttributeNames"] = names
            self._db.datasets.raw_update_item(**kwargs)
            return ResponseModel(success=True, message="Dataset updated")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _delete(self, req: RequestResourceModel) -> ResponseModel:
        try:
            org_id = self._get_org_id(req.user_id)
            dataset_id = req.data.get("dataset_id")
            self._db.datasets.delete_by_key({"org_id": org_id, "id": dataset_id})
            return ResponseModel(success=True, message="Dataset deleted")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
