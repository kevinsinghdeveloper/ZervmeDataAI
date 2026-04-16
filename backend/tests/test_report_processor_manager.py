"""Unit tests for ReportProcessorResourceManager."""
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

def _build_service_managers(etl_mock=None):
    """Build service_managers dict with a mock ETL service and DB."""
    mock_db = MagicMock()

    # users repo
    user_obj = MagicMock()
    user_obj.org_id = SAMPLE_USER_ITEM["org_id"]
    user_obj.id = SAMPLE_USER_ITEM["id"]
    mock_db.users.get_by_id.return_value = user_obj

    # report_jobs repo
    mock_db.report_jobs.create.return_value = {}
    mock_db.report_jobs.raw_update_item.return_value = {}
    mock_db.report_jobs.get_by_key.return_value = None

    mock_etl = etl_mock or MagicMock()
    return {"db": mock_db, "etl": mock_etl}


# ---------------------------------------------------------------------------
# START JOB
# ---------------------------------------------------------------------------

def test_start_job_success():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    mock_etl = MagicMock()
    mock_etl.run_report.return_value = {
        "status": "success",
        "message": "my_report completed.",
    }

    svc = _build_service_managers(etl_mock=mock_etl)
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.post(make_request({
        "action": "start_job",
        "report_name": "my_report",
        "task_params": {"param1": "value1"},
        "llm_config": {"ai_type": "openai"},
    }))

    assert resp.success is True
    assert resp.status_code == 201
    assert "job" in resp.data
    assert resp.data["job"]["status"] == "completed"

    mock_etl.run_report.assert_called_once_with(
        "my_report",
        {"param1": "value1"},
        {"ai_type": "openai"},
    )
    # Verify job was persisted
    svc["db"].report_jobs.create.assert_called_once()


def test_start_job_missing_report_name():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.post(make_request({
        "action": "start_job",
        # report_name intentionally omitted
        "task_params": {},
    }))

    assert resp.success is False
    assert resp.status_code == 400
    assert "report_name" in resp.error.lower()


def test_start_job_defaults_empty_params():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    mock_etl = MagicMock()
    mock_etl.run_report.return_value = {"status": "success"}

    svc = _build_service_managers(etl_mock=mock_etl)
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.post(make_request({
        "action": "start_job",
        "report_name": "my_report",
    }))

    assert resp.success is True
    mock_etl.run_report.assert_called_once_with("my_report", {}, {})


def test_start_job_etl_exception():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    mock_etl = MagicMock()
    mock_etl.run_report.side_effect = Exception("ETL processing failed")

    svc = _build_service_managers(etl_mock=mock_etl)
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.post(make_request({
        "action": "start_job",
        "report_name": "broken_report",
    }))

    assert resp.success is False
    assert resp.status_code == 500
    assert "ETL processing failed" in resp.error


# ---------------------------------------------------------------------------
# GET STATUS
# ---------------------------------------------------------------------------

def test_get_status_success():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    # Mock DB to return a job item
    svc["db"].report_jobs.get_by_key.return_value = {
        "org_id": "org-456",
        "id": "job-123",
        "report_id": "report-1",
        "status": "completed",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }

    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.get(make_request({
        "action": "get_status",
        "job_id": "job-123",
    }))

    assert resp.success is True
    assert resp.data["job"]["id"] == "job-123"
    assert resp.data["job"]["status"] == "completed"
    svc["db"].report_jobs.get_by_key.assert_called_once_with(
        {"org_id": "org-456", "id": "job-123"}
    )


def test_get_status_not_found():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    svc["db"].report_jobs.get_by_key.return_value = None

    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.get(make_request({
        "action": "get_status",
        "job_id": "nonexistent-job",
    }))

    assert resp.success is False
    assert resp.status_code == 404


def test_get_status_missing_job_id():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.get(make_request({
        "action": "get_status",
        # job_id intentionally omitted
    }))

    assert resp.success is False
    assert resp.status_code == 400
    assert "job_id" in resp.error.lower()


# ---------------------------------------------------------------------------
# STOP JOB
# ---------------------------------------------------------------------------

def test_stop_job_success():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.post(make_request({
        "action": "stop_job",
        "job_id": "job-456",
    }))

    assert resp.success is True
    assert "job-456" in resp.message


def test_stop_job_missing_job_id():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.post(make_request({
        "action": "stop_job",
        # job_id intentionally omitted
    }))

    assert resp.success is False
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Invalid actions
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.get(make_request({"action": "nonexistent"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.post(make_request({"action": "nonexistent"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_put_returns_invalid():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.put(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_delete_returns_invalid():
    from managers.report_processor.ReportProcessorResourceManager import (
        ReportProcessorResourceManager,
    )

    svc = _build_service_managers()
    mgr = ReportProcessorResourceManager(service_managers=svc)

    resp = mgr.delete(make_request({"action": "anything"}))

    assert resp.success is False
    assert resp.status_code == 400
