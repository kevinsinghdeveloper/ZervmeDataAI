"""Notification Resource Manager."""
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from abstractions.IResourceManager import IResourceManager
from abstractions.models.ResponseModel import ResponseModel
from abstractions.models.RequestResourceModel import RequestResourceModel
from database.schemas.notification import NotificationItem


class NotificationResourceManager(IResourceManager):
    def get(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "list":
            return self._list(req)
        elif action == "unread_count":
            return self._unread_count(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def post(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "read_all":
            return self._read_all(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def put(self, req: RequestResourceModel) -> ResponseModel:
        action = req.data.get("action", "")
        if action == "mark_read":
            return self._mark_read(req)
        return ResponseModel(success=False, error="Invalid action", status_code=400)

    def delete(self, req): return ResponseModel(success=False, error="Not implemented", status_code=405)

    def _list(self, req):
        try:
            user_id = str(req.user_id)
            resp = self._db.notifications.raw_query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False, Limit=50)
            notifs = [NotificationItem.from_item(i).to_api_dict() for i in resp.get("Items", [])]
            return ResponseModel(success=True, data={"notifications": notifs})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _unread_count(self, req):
        try:
            user_id = str(req.user_id)
            resp = self._db.notifications.raw_query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                FilterExpression=Attr("is_read").eq(False),
                Select="COUNT")
            return ResponseModel(success=True, data={"unreadCount": resp.get("Count", 0)})
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _mark_read(self, req):
        try:
            user_id = str(req.user_id)
            notif_id = req.data.get("notification_id")
            self._db.notifications.raw_update_item(
                Key={"user_id": user_id, "timestamp_id": notif_id},
                UpdateExpression="SET is_read = :r",
                ExpressionAttributeValues={":r": True})
            return ResponseModel(success=True, message="Marked as read")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)

    def _read_all(self, req):
        try:
            user_id = str(req.user_id)
            resp = self._db.notifications.raw_query(
                KeyConditionExpression=Key("user_id").eq(user_id),
                FilterExpression=Attr("is_read").eq(False))
            for item in resp.get("Items", []):
                self._db.notifications.raw_update_item(
                    Key={"user_id": user_id, "timestamp_id": item["timestamp_id"]},
                    UpdateExpression="SET is_read = :r",
                    ExpressionAttributeValues={":r": True})
            return ResponseModel(success=True, message="All notifications marked as read")
        except Exception as e:
            return ResponseModel(success=False, error=str(e), status_code=500)
