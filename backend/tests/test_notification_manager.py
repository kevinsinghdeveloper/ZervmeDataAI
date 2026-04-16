"""Unit tests for NotificationResourceManager."""
import sys
import os
import pytest
from unittest.mock import MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from managers.notifications.NotificationResourceManager import NotificationResourceManager
from tests.conftest import make_request, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_NOTIFICATION_ITEM = {
    "user_id": "user-123",
    "timestamp_id": "2024-01-15T10:00:00#notif-1",
    "org_id": "org-456",
    "notification_type": "info",
    "title": "Test Notification",
    "message": "You have a new update",
    "is_read": False,
    "action_url": None,
    "metadata": None,
    "expires_at_ttl": 1713200000,
    "created_at": "2024-01-15T10:00:00",
}

SAMPLE_READ_NOTIFICATION_ITEM = {
    **SAMPLE_NOTIFICATION_ITEM,
    "timestamp_id": "2024-01-14T09:00:00#notif-2",
    "title": "Old Notification",
    "is_read": True,
}


def _build_mock_db(notifications_items=None, notifications_count=None):
    """Build a mock db service with a preconfigured notifications repo."""
    mock_db = MagicMock()
    mock_notifications = mock_db.notifications
    mock_notifications.raw_query.return_value = {
        "Items": notifications_items or [],
        "Count": notifications_count if notifications_count is not None else len(notifications_items or []),
    }
    mock_notifications.raw_update_item.return_value = {}
    return mock_db


# ---------------------------------------------------------------------------
# LIST notifications
# ---------------------------------------------------------------------------

def test_list_notifications_success():
    mock_db = _build_mock_db(notifications_items=[SAMPLE_NOTIFICATION_ITEM])

    mgr = NotificationResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is True
    assert "notifications" in resp.data
    assert len(resp.data["notifications"]) == 1
    assert resp.data["notifications"][0]["title"] == "Test Notification"
    assert resp.data["notifications"][0]["type"] == "info"


def test_list_notifications_empty():
    mock_db = _build_mock_db(notifications_items=[])

    mgr = NotificationResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is True
    assert resp.data["notifications"] == []


# ---------------------------------------------------------------------------
# UNREAD count
# ---------------------------------------------------------------------------

def test_unread_count_success():
    mock_db = _build_mock_db(notifications_count=3)

    mgr = NotificationResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "unread_count"}))

    assert resp.success is True
    assert resp.data["unreadCount"] == 3


def test_unread_count_zero():
    mock_db = _build_mock_db(notifications_count=0)

    mgr = NotificationResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "unread_count"}))

    assert resp.success is True
    assert resp.data["unreadCount"] == 0


# ---------------------------------------------------------------------------
# MARK READ (single)
# ---------------------------------------------------------------------------

def test_mark_read_success():
    mock_db = _build_mock_db()

    mgr = NotificationResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({
        "action": "mark_read",
        "notification_id": "2024-01-15T10:00:00#notif-1",
    }))

    assert resp.success is True
    assert resp.message == "Marked as read"
    mock_db.notifications.raw_update_item.assert_called_once_with(
        Key={"user_id": "user-123", "timestamp_id": "2024-01-15T10:00:00#notif-1"},
        UpdateExpression="SET is_read = :r",
        ExpressionAttributeValues={":r": True},
    )


# ---------------------------------------------------------------------------
# READ ALL
# ---------------------------------------------------------------------------

def test_read_all_success():
    unread_1 = {**SAMPLE_NOTIFICATION_ITEM, "timestamp_id": "2024-01-15T10:00:00#notif-1"}
    unread_2 = {**SAMPLE_NOTIFICATION_ITEM, "timestamp_id": "2024-01-15T11:00:00#notif-2"}

    mock_db = _build_mock_db(notifications_items=[unread_1, unread_2])

    mgr = NotificationResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "read_all"}))

    assert resp.success is True
    assert resp.message == "All notifications marked as read"
    assert mock_db.notifications.raw_update_item.call_count == 2
    mock_db.notifications.raw_update_item.assert_any_call(
        Key={"user_id": "user-123", "timestamp_id": "2024-01-15T10:00:00#notif-1"},
        UpdateExpression="SET is_read = :r",
        ExpressionAttributeValues={":r": True},
    )
    mock_db.notifications.raw_update_item.assert_any_call(
        Key={"user_id": "user-123", "timestamp_id": "2024-01-15T11:00:00#notif-2"},
        UpdateExpression="SET is_read = :r",
        ExpressionAttributeValues={":r": True},
    )


def test_read_all_none_unread():
    mock_db = _build_mock_db(notifications_items=[])

    mgr = NotificationResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "read_all"}))

    assert resp.success is True
    assert resp.message == "All notifications marked as read"
    mock_db.notifications.raw_update_item.assert_not_called()


# ---------------------------------------------------------------------------
# DELETE not implemented
# ---------------------------------------------------------------------------

def test_delete_not_implemented():
    mgr = NotificationResourceManager()
    resp = mgr.delete(make_request({"action": "remove"}))

    assert resp.success is False
    assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Invalid actions
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    mgr = NotificationResourceManager()
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    mgr = NotificationResourceManager()
    resp = mgr.post(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
