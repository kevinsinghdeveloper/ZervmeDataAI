from datetime import datetime
from abstractions.IResourceManager import IResourceManager
from abstractions.models.RequestResourceModel import RequestResourceModel
from abstractions.models.ResponseModel import ResponseModel
from database.schemas.audit_log import AuditLogItem


class AuditResourceManager(IResourceManager):
    def get(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        action = request_resource_model.data.get("action")

        if action == "list_logs":
            return self._list_audit_logs(request_resource_model)
        elif action == "get_log":
            return self._get_audit_log(request_resource_model)

        return ResponseModel(success=False, error="Unknown action", status_code=400)

    def post(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not supported", status_code=405)

    def put(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not supported", status_code=405)

    def delete(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        return ResponseModel(success=False, error="Method not supported", status_code=405)

    def _list_audit_logs(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = request_resource_model.user_id
        data = request_resource_model.data
        page = data.get("page", 1)
        per_page = data.get("per_page", 50)
        action_filter = data.get("action_filter")
        user_filter = data.get("user_filter")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        try:
            # Verify requesting user is admin
            requesting_user = self._db.users.get_by_id(str(user_id))
            if not requesting_user or not getattr(requesting_user, "is_super_admin", False):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            # Build filter expression for scan
            filter_parts = []
            expr_attr_values = {}
            expr_attr_names = {}

            if action_filter:
                filter_parts.append("#act = :action_filter")
                expr_attr_values[":action_filter"] = action_filter
                expr_attr_names["#act"] = "action"

            if user_filter:
                filter_parts.append("user_id = :user_filter")
                expr_attr_values[":user_filter"] = user_filter

            if start_date:
                try:
                    datetime.fromisoformat(start_date)
                    filter_parts.append("#ts >= :start_date")
                    expr_attr_values[":start_date"] = start_date
                    expr_attr_names["#ts"] = "timestamp"
                except ValueError:
                    pass

            if end_date:
                try:
                    datetime.fromisoformat(end_date)
                    filter_parts.append("#ts <= :end_date")
                    expr_attr_values[":end_date"] = end_date
                    expr_attr_names["#ts"] = "timestamp"
                except ValueError:
                    pass

            scan_kwargs = {}

            if filter_parts:
                scan_kwargs["FilterExpression"] = " AND ".join(filter_parts)
            if expr_attr_values:
                scan_kwargs["ExpressionAttributeValues"] = expr_attr_values
            if expr_attr_names:
                scan_kwargs["ExpressionAttributeNames"] = expr_attr_names

            # Scan all matching items for total count and pagination
            all_items = []
            while True:
                response = self._db.audit_logs.raw_scan(**scan_kwargs)
                all_items.extend(response.get("Items", []))
                last_key = response.get("LastEvaluatedKey")
                if not last_key:
                    break
                scan_kwargs["ExclusiveStartKey"] = last_key

            # Sort by timestamp descending
            all_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            total = len(all_items)
            start = (page - 1) * per_page
            end = start + per_page
            page_items = all_items[start:end]

            logs = [AuditLogItem.from_item(item).to_api_dict() for item in page_items]

            return ResponseModel(
                success=True,
                data={
                    "logs": logs,
                    "total": total,
                    "page": page,
                    "perPage": per_page,
                },
            )
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _get_audit_log(self, request_resource_model: RequestResourceModel) -> ResponseModel:
        user_id = request_resource_model.user_id
        log_id = request_resource_model.data.get("log_id")

        try:
            # Verify requesting user is admin
            requesting_user = self._db.users.get_by_id(str(user_id))
            if not requesting_user or not getattr(requesting_user, "is_super_admin", False):
                return ResponseModel(success=False, error="Admin access required", status_code=403)

            # audit_log table has composite key (id + timestamp), so query by id
            from boto3.dynamodb.conditions import Key
            resp = self._db.audit_logs.raw_query(KeyConditionExpression=Key("id").eq(log_id))
            items = resp.get("Items", [])
            if not items:
                return ResponseModel(success=False, error="Audit log not found", status_code=404)

            item = items[0]
            log = AuditLogItem.from_item(item)
            return ResponseModel(success=True, data=log.to_api_dict())
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
