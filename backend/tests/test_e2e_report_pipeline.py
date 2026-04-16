"""End-to-end test for the report pipeline.

Tests the full flow: create project → create report → start job →
check status → get dashboard — all with mocked DB and LLM.
"""
import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from tests.conftest import make_request, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Shared mock helpers
# ---------------------------------------------------------------------------

def _build_mock_db():
    """Build a realistic mock db with all repos needed for the pipeline."""
    mock_db = MagicMock()

    # users repo
    user_obj = MagicMock()
    user_obj.org_id = SAMPLE_USER_ITEM["org_id"]
    user_obj.id = SAMPLE_USER_ITEM["id"]
    mock_db.users.get_by_id.return_value = user_obj

    # projects repo
    mock_db.projects.create.return_value = {}
    mock_db.projects.list_all.return_value = []

    # reports repo
    mock_db.reports.create.return_value = {}
    mock_db.reports.list_all.return_value = []
    mock_db.reports.get_by_key.return_value = None

    # report_jobs repo
    mock_db.report_jobs.create.return_value = {}
    mock_db.report_jobs.list_all.return_value = []
    mock_db.report_jobs.get_by_key.return_value = None

    # report_cache repo
    mock_db.report_cache.create.return_value = {}
    mock_db.report_cache.get_by_key.return_value = None

    return mock_db


# ---------------------------------------------------------------------------
# E2E pipeline test
# ---------------------------------------------------------------------------

def test_full_report_pipeline():
    """Test the complete flow: project → report → job → status."""
    from managers.projects.ProjectResourceManager import ProjectResourceManager
    from managers.reports.ReportResourceManager import ReportResourceManager
    from managers.report_processor.ReportProcessorResourceManager import ReportProcessorResourceManager

    mock_db = _build_mock_db()
    mock_etl = MagicMock()

    svc = {"db": mock_db, "etl": mock_etl}

    # --- Step 1: Create a project ---
    project_mgr = ProjectResourceManager(service_managers=svc)
    proj_resp = project_mgr.post(make_request({
        "action": "create",
        "name": "CI Research",
        "description": "Competitive intelligence research project",
        "projectType": "Competitive Intelligence",
    }))
    assert proj_resp.success is True
    assert proj_resp.status_code == 201
    mock_db.projects.create.assert_called_once()

    # --- Step 2: Create a report ---
    report_mgr = ReportResourceManager(service_managers=svc)
    report_resp = report_mgr.post(make_request({
        "action": "create",
        "name": "Brand Power Analysis",
        "projectId": "proj-1",
        "reportTypeId": "brand_power",
        "modelId": "model-1",
        "datasetConfig": {"industry": "Technology"},
        "reportConfig": {"companies": ["Company A", "Company B"]},
    }))
    assert report_resp.success is True
    assert report_resp.status_code == 201
    assert report_resp.data["report"]["name"] == "Brand Power Analysis"
    mock_db.reports.create.assert_called_once()

    # --- Step 3: Start a report job ---
    mock_etl.run_report.return_value = {
        "status": "success",
        "message": "brand_power completed.",
        "data": {"scores": [85, 72, 91]},
    }

    processor_mgr = ReportProcessorResourceManager(service_managers=svc)
    job_resp = processor_mgr.post(make_request({
        "action": "start_job",
        "report_name": "brand_power",
        "report_id": "report-1",
        "task_params": {"industry": "Technology", "companies": ["A", "B"]},
        "llm_config": {"ai_type": "openai", "model": "gpt-4"},
    }))
    assert job_resp.success is True
    assert job_resp.status_code == 201
    assert "job" in job_resp.data
    assert job_resp.data["job"]["status"] == "completed"

    mock_etl.run_report.assert_called_once_with(
        "brand_power",
        {"industry": "Technology", "companies": ["A", "B"]},
        {"ai_type": "openai", "model": "gpt-4"},
    )

    # Verify job was persisted to DB
    mock_db.report_jobs.create.assert_called_once()

    # --- Step 4: Check job status ---
    # The get_status now reads from DB, so set up the mock
    job_id = job_resp.data["job"]["id"]
    mock_db.report_jobs.get_by_key.return_value = {
        "org_id": "org-456",
        "id": job_id,
        "report_id": "report-1",
        "status": "completed",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }

    status_resp = processor_mgr.get(make_request({
        "action": "get_status",
        "job_id": job_id,
    }))
    assert status_resp.success is True
    assert status_resp.data["job"]["status"] == "completed"


def test_pipeline_etl_failure_is_reported():
    """When ETL fails, the start_job should return an error."""
    from managers.report_processor.ReportProcessorResourceManager import ReportProcessorResourceManager

    mock_db = _build_mock_db()
    mock_etl = MagicMock()
    mock_etl.run_report.side_effect = Exception("LLM API rate limited")

    svc = {"db": mock_db, "etl": mock_etl}

    processor_mgr = ReportProcessorResourceManager(service_managers=svc)
    job_resp = processor_mgr.post(make_request({
        "action": "start_job",
        "report_name": "brand_power",
        "task_params": {},
        "llm_config": {"ai_type": "openai"},
    }))

    assert job_resp.success is False
    assert job_resp.status_code == 500
    assert "LLM API rate limited" in job_resp.error


def test_pipeline_report_crud_lifecycle():
    """Test create → list → get → delete lifecycle for reports."""
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db()
    svc = {"db": mock_db}

    mgr = ReportResourceManager(service_managers=svc)

    # Create
    create_resp = mgr.post(make_request({
        "action": "create",
        "name": "Lifecycle Report",
        "projectId": "proj-1",
    }))
    assert create_resp.success is True
    assert create_resp.status_code == 201

    # List — mock the DB to return the created report
    mock_db.reports.list_all.return_value = [{
        "org_id": "org-456",
        "id": "report-new",
        "name": "Lifecycle Report",
        "project_id": "proj-1",
        "status": "draft",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }]
    list_resp = mgr.get(make_request({"action": "list"}))
    assert list_resp.success is True
    assert len(list_resp.data["reports"]) == 1
    assert list_resp.data["reports"][0]["name"] == "Lifecycle Report"

    # Get
    mock_db.reports.get_by_key.return_value = {
        "org_id": "org-456",
        "id": "report-new",
        "name": "Lifecycle Report",
        "project_id": "proj-1",
        "status": "draft",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    get_resp = mgr.get(make_request({"action": "get", "report_id": "report-new"}))
    assert get_resp.success is True
    assert get_resp.data["report"]["id"] == "report-new"

    # Delete
    delete_resp = mgr.delete(make_request({"action": "delete", "report_id": "report-new"}))
    assert delete_resp.success is True
    mock_db.reports.delete_by_key.assert_called_once()


def test_pipeline_project_to_report_association():
    """Reports should be filterable by project_id."""
    from managers.reports.ReportResourceManager import ReportResourceManager

    mock_db = _build_mock_db()
    mock_db.reports.list_all.return_value = [
        {
            "org_id": "org-456", "id": "r-1", "name": "Report A",
            "project_id": "proj-1", "status": "active",
            "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
        },
        {
            "org_id": "org-456", "id": "r-2", "name": "Report B",
            "project_id": "proj-2", "status": "active",
            "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
        },
        {
            "org_id": "org-456", "id": "r-3", "name": "Report C",
            "project_id": "proj-1", "status": "active",
            "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
        },
    ]
    svc = {"db": mock_db}
    mgr = ReportResourceManager(service_managers=svc)

    resp = mgr.get(make_request({"action": "list", "project_id": "proj-1"}))
    assert resp.success is True
    assert len(resp.data["reports"]) == 2
    assert all(r["projectId"] == "proj-1" for r in resp.data["reports"])
