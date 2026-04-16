"""Unit tests for ReportResourceManager."""
import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from tests.conftest import make_request, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_REPORT_ITEM = {
    "org_id": "org-456",
    "id": "report-1",
    "name": "Quarterly Analysis",
    "project_id": "proj-1",
    "report_type_id": "rtype-1",
    "model_id": "model-1",
    "dataset_config": '{"source": "s3://bucket/data.csv"}',
    "report_config": '{"output_format": "pdf"}',
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_REPORT_ITEM_2 = {
    "org_id": "org-456",
    "id": "report-2",
    "name": "Monthly Summary",
    "project_id": "proj-2",
    "report_type_id": "rtype-2",
    "model_id": "model-1",
    "status": "active",
    "created_at": "2024-02-01T00:00:00",
    "updated_at": "2024-02-01T00:00:00",
}


def _build_mock_db(users_item=None, reports_items=None):
    """Build a mock db object with repo attributes."""
    mock_db = MagicMock()

    # users repo
    if users_item:
        user_obj = MagicMock()
        user_obj.org_id = users_item.get("org_id")
        user_obj.id = users_item.get("id")
        mock_db.users.get_by_id.return_value = user_obj
    else:
        mock_db.users.get_by_id.return_value = None

    # reports repo
    mock_db.reports.list_all.return_value = reports_items or []
    mock_db.reports.get_by_key.return_value = (
        reports_items[0] if reports_items else None
    )
    mock_db.reports.create.return_value = {}
    mock_db.reports.raw_update_item.return_value = {}
    mock_db.reports.delete_by_key.return_value = {}

    return mock_db


# ---------------------------------------------------------------------------
# LIST reports
# ---------------------------------------------------------------------------

def test_list_reports_success():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        reports_items=[SAMPLE_REPORT_ITEM, SAMPLE_REPORT_ITEM_2],
    )

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is True
    assert "reports" in resp.data
    assert len(resp.data["reports"]) == 2
    assert resp.data["reports"][0]["name"] == "Quarterly Analysis"
    assert resp.data["reports"][1]["name"] == "Monthly Summary"
    mock_db.reports.list_all.assert_called_once_with(org_id="org-456")


def test_list_reports_filtered_by_project():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        reports_items=[SAMPLE_REPORT_ITEM, SAMPLE_REPORT_ITEM_2],
    )

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list", "project_id": "proj-1"}))

    assert resp.success is True
    assert len(resp.data["reports"]) == 1
    assert resp.data["reports"][0]["projectId"] == "proj-1"


def test_list_reports_no_org():
    from managers.reports.ReportResourceManager import ReportResourceManager

    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET single report
# ---------------------------------------------------------------------------

def test_get_report_success():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        reports_items=[SAMPLE_REPORT_ITEM],
    )

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "report_id": "report-1"}))

    assert resp.success is True
    assert resp.data["report"]["id"] == "report-1"
    assert resp.data["report"]["name"] == "Quarterly Analysis"
    mock_db.reports.get_by_key.assert_called_once_with(
        {"org_id": "org-456", "id": "report-1"}
    )


def test_get_report_not_found():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM, reports_items=[])
    mock_db.reports.get_by_key.return_value = None

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "report_id": "nonexistent"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# CREATE report
# ---------------------------------------------------------------------------

def test_create_report_success():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({
        "action": "create",
        "name": "New Report",
        "projectId": "proj-1",
        "reportTypeId": "rtype-1",
        "modelId": "model-1",
        "datasetConfig": {"source": "s3://bucket/new.csv"},
        "reportConfig": {"output_format": "html"},
    }))

    assert resp.success is True
    assert resp.status_code == 201
    assert resp.data["report"]["name"] == "New Report"
    assert resp.data["report"]["projectId"] == "proj-1"
    mock_db.reports.create.assert_called_once()

    # Verify the item dict passed to create has the right org_id
    created_item = mock_db.reports.create.call_args[0][0]
    assert created_item["org_id"] == "org-456"
    assert created_item["name"] == "New Report"


def test_create_report_no_org():
    from managers.reports.ReportResourceManager import ReportResourceManager

    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "create", "name": "Orphan Report"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE report
# ---------------------------------------------------------------------------

def test_delete_report_success():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.delete(make_request({"action": "delete", "report_id": "report-1"}))

    assert resp.success is True
    mock_db.reports.delete_by_key.assert_called_once_with(
        {"org_id": "org-456", "id": "report-1"}
    )


# ---------------------------------------------------------------------------
# Invalid action
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = MagicMock()

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = MagicMock()

    mgr = ReportResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
