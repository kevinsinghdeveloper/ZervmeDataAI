"""Unit tests for AdminResourceManager (legacy stub)."""
import pytest
from unittest.mock import MagicMock

from managers.admin.AdminResourceManager import AdminResourceManager
from tests.conftest import make_request


def _build_manager(mock_db=None):
    """Instantiate AdminResourceManager with a mock db service."""
    if mock_db is None:
        mock_db = MagicMock()
    mgr = AdminResourceManager(service_managers={"db": mock_db})
    return mgr


# ===========================================================================
# DASHBOARD
# ===========================================================================

class TestAdminDashboard:

    def test_get_dashboard_success(self):
        mock_db = MagicMock()
        mock_db.users.raw_scan.return_value = {"Count": 42}
        mock_db.organizations.raw_scan.return_value = {"Count": 7}

        mgr = _build_manager(mock_db)

        req = make_request(data={"action": "dashboard"}, user_id="admin-789")
        resp = mgr.get(req)

        assert resp.success is True
        assert resp.status_code == 200
        assert resp.data["totalUsers"] == 42
        assert resp.data["totalOrganizations"] == 7

    def test_get_dashboard_error(self):
        mock_db = MagicMock()
        mock_db.users.raw_scan.side_effect = Exception("DynamoDB timeout")

        mgr = _build_manager(mock_db)

        req = make_request(data={"action": "dashboard"}, user_id="admin-789")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 500


# ===========================================================================
# INVALID GET ACTION
# ===========================================================================

class TestAdminInvalidAction:

    def test_get_invalid_action(self):
        mgr = _build_manager()

        req = make_request(data={"action": "nonexistent"}, user_id="admin-789")
        resp = mgr.get(req)

        assert resp.success is False
        assert resp.status_code == 400


# ===========================================================================
# DEPRECATED METHODS (410 Gone)
# ===========================================================================

class TestAdminDeprecated:

    def test_post_deprecated(self):
        mgr = _build_manager()

        req = make_request(data={"action": "anything"}, user_id="admin-789")
        resp = mgr.post(req)

        assert resp.success is False
        assert resp.status_code == 410
        assert "deprecated" in resp.error.lower()

    def test_put_deprecated(self):
        mgr = _build_manager()

        req = make_request(data={"action": "anything"}, user_id="admin-789")
        resp = mgr.put(req)

        assert resp.success is False
        assert resp.status_code == 410
        assert "deprecated" in resp.error.lower()

    def test_delete_deprecated(self):
        mgr = _build_manager()

        req = make_request(data={"action": "anything"}, user_id="admin-789")
        resp = mgr.delete(req)

        assert resp.success is False
        assert resp.status_code == 410
        assert "deprecated" in resp.error.lower()
