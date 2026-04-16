"""Unit tests for ConfigResourceManager."""
import sys
import os
import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from tests.conftest import make_request, SAMPLE_ADMIN_USER_ITEM, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_THEME_ITEM = {
    "pk": "CONFIG",
    "sk": "theme",
    "primaryColor": "#1976d2",
    "secondaryColor": "#dc004e",
    "backgroundColor": "#0f172a",
    "paperColor": "#1e293b",
    "textColor": "#333333",
    "logoUrl": "",
    "faviconUrl": "",
    "appName": "Zerve Direct",
    "fontFamily": "Inter, system-ui, sans-serif",
}

SAMPLE_SETTINGS_ITEM = {
    "pk": "CONFIG",
    "sk": "settings",
    "allowPublicChat": True,
    "requireEmailVerification": False,
    "maxUploadSizeMb": 50,
    "defaultModel": "gpt-4",
    "enableAuditLogging": True,
    "chatbotSystemPrompt": "You are a helpful assistant.",
}

ADMIN_USER = SimpleNamespace(**{**SAMPLE_ADMIN_USER_ITEM, "id": "admin-789", "is_super_admin": True})
NON_ADMIN_USER = SimpleNamespace(**{**SAMPLE_USER_ITEM, "id": "user-123", "is_super_admin": False})


def _build_mock_db(users_item=None, config_item=None):
    """Build a mock db service with users and config repos."""
    db = MagicMock()
    db.users.get_by_id.return_value = users_item
    db.users.scan_count.return_value = 0
    db.users.create.return_value = None
    db.config.get_config.return_value = config_item
    db.config.put_config.return_value = None
    return db


def _mgr(db=None):
    from managers.config.ConfigResourceManager import ConfigResourceManager
    return ConfigResourceManager(service_managers={"db": db or _build_mock_db()})


# ---------------------------------------------------------------------------
# GET - get_theme (existing)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("uploads_bucket", [""])
def test_get_theme_existing(uploads_bucket, monkeypatch):
    monkeypatch.setenv("UPLOADS_BUCKET", uploads_bucket)
    db = _build_mock_db(config_item=SAMPLE_THEME_ITEM)
    mgr = _mgr(db)
    resp = mgr.get(make_request({"action": "get_theme"}))

    assert resp.success is True
    assert "primaryColor" in resp.data
    assert resp.data["primaryColor"] == "#1976d2"
    # pk/sk should be stripped from the response
    assert "pk" not in resp.data
    assert "sk" not in resp.data


# ---------------------------------------------------------------------------
# GET - get_theme (defaults when no item exists)
# ---------------------------------------------------------------------------

def test_get_theme_defaults(monkeypatch):
    monkeypatch.setenv("UPLOADS_BUCKET", "")
    db = _build_mock_db(config_item=None)
    mgr = _mgr(db)
    resp = mgr.get(make_request({"action": "get_theme"}))

    assert resp.success is True
    assert "primaryColor" in resp.data
    assert resp.data["primaryColor"] == "#1976d2"
    assert resp.data["appName"] == "Zerve Direct"


# ---------------------------------------------------------------------------
# GET - get_settings (existing)
# ---------------------------------------------------------------------------

def test_get_settings_existing():
    db = _build_mock_db(config_item=SAMPLE_SETTINGS_ITEM)
    mgr = _mgr(db)
    resp = mgr.get(make_request({"action": "get_settings"}))

    assert resp.success is True
    assert resp.data["allowPublicChat"] is True
    assert "pk" not in resp.data
    assert "sk" not in resp.data


# ---------------------------------------------------------------------------
# GET - get_settings (defaults)
# ---------------------------------------------------------------------------

def test_get_settings_defaults():
    db = _build_mock_db(config_item=None)
    mgr = _mgr(db)
    resp = mgr.get(make_request({"action": "get_settings"}))

    assert resp.success is True
    assert resp.data["allowPublicChat"] is True
    assert resp.data["maxUploadSizeMb"] == 50


# ---------------------------------------------------------------------------
# POST - update_theme (admin success)
# ---------------------------------------------------------------------------

def test_update_theme_success(monkeypatch):
    monkeypatch.setenv("UPLOADS_BUCKET", "")
    db = _build_mock_db(users_item=ADMIN_USER, config_item=SAMPLE_THEME_ITEM)
    mgr = _mgr(db)
    resp = mgr.post(make_request(
        {"action": "update_theme", "primaryColor": "#ff0000"},
        user_id="admin-789",
    ))

    assert resp.success is True
    assert resp.message == "Theme updated"
    assert resp.data["primaryColor"] == "#ff0000"
    db.config.put_config.assert_called_once()


# ---------------------------------------------------------------------------
# POST - update_theme (non-admin rejected)
# ---------------------------------------------------------------------------

def test_update_theme_non_admin(monkeypatch):
    monkeypatch.setenv("UPLOADS_BUCKET", "")
    db = _build_mock_db(users_item=NON_ADMIN_USER, config_item=SAMPLE_THEME_ITEM)
    mgr = _mgr(db)
    resp = mgr.post(make_request(
        {"action": "update_theme", "primaryColor": "#ff0000"},
        user_id="user-123",
    ))

    assert resp.success is False
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST - update_settings (admin success)
# ---------------------------------------------------------------------------

def test_update_settings_success():
    db = _build_mock_db(users_item=ADMIN_USER, config_item=SAMPLE_SETTINGS_ITEM)
    mgr = _mgr(db)
    resp = mgr.post(make_request(
        {"action": "update_settings", "allowPublicChat": False},
        user_id="admin-789",
    ))

    assert resp.success is True
    assert resp.message == "Settings updated"
    assert resp.data["allowPublicChat"] is False
    db.config.put_config.assert_called_once()


# ---------------------------------------------------------------------------
# POST - update_settings (non-admin rejected)
# ---------------------------------------------------------------------------

def test_update_settings_non_admin():
    db = _build_mock_db(users_item=NON_ADMIN_USER, config_item=SAMPLE_SETTINGS_ITEM)
    mgr = _mgr(db)
    resp = mgr.post(make_request(
        {"action": "update_settings", "allowPublicChat": False},
        user_id="user-123",
    ))

    assert resp.success is False
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT / DELETE - not supported
# ---------------------------------------------------------------------------

def test_put_not_supported():
    mgr = _mgr()
    resp = mgr.put(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 405


def test_delete_not_supported():
    mgr = _mgr()
    resp = mgr.delete(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Invalid action
# ---------------------------------------------------------------------------

def test_invalid_get_action():
    mgr = _mgr()
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
