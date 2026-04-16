"""Unit tests for NotificationService."""
import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.notification.NotificationService import NotificationService


def _build_service():
    mock_db = MagicMock()
    svc = NotificationService()
    svc.set_db(mock_db)
    svc.initialize()
    return svc, mock_db


class TestNotificationServiceSend:
    def test_send_creates_notification(self):
        svc, mock_db = _build_service()
        result = svc.send("u-1", "info", "Test Title", "Test message", org_id="org-1", action_url="/test")
        mock_db.notifications.create.assert_called_once()
        assert result.user_id == "u-1"
        assert result.title == "Test Title"
        assert result.notification_type == "info"

    def test_send_without_optional_fields(self):
        svc, mock_db = _build_service()
        result = svc.send("u-1", "system", "Title", "Body")
        mock_db.notifications.create.assert_called_once()
        assert result.org_id is None
        assert result.action_url is None

    def test_send_timesheet_reminder(self):
        svc, mock_db = _build_service()
        result = svc.send_timesheet_reminder("u-1", "org-1")
        mock_db.notifications.create.assert_called_once()
        assert result.notification_type == "timesheet_reminder"
        assert result.action_url == "/timesheet"

    def test_send_approval_notification_approved(self):
        svc, mock_db = _build_service()
        result = svc.send_approval_notification("u-1", "org-1", "approved")
        assert result.notification_type == "timesheet_approved"
        assert "approved" in result.message

    def test_send_approval_notification_rejected(self):
        svc, mock_db = _build_service()
        result = svc.send_approval_notification("u-1", "org-1", "rejected")
        assert result.notification_type == "timesheet_rejected"
        assert "rejected" in result.message
