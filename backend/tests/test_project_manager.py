"""Unit tests for ProjectResourceManager."""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.models.RequestResourceModel import RequestResourceModel
from tests.conftest import make_request, SAMPLE_USER_ITEM


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

SAMPLE_PROJECT_ITEM = {
    "org_id": "org-456",
    "id": "proj-1",
    "name": "Project Alpha",
    "project_type": "ai_report",
    "description": "Main project",
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}


def _build_mock_db(users_item=None, projects_items=None):
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

    # projects repo
    mock_db.projects.list_all.return_value = projects_items or []
    mock_db.projects.get_by_key.return_value = (projects_items[0] if projects_items else None)
    mock_db.projects.create.return_value = {}
    mock_db.projects.raw_update_item.return_value = {}
    mock_db.projects.delete_by_key.return_value = {}

    return mock_db


# ---------------------------------------------------------------------------
# LIST projects
# ---------------------------------------------------------------------------

def test_list_projects_success():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        projects_items=[SAMPLE_PROJECT_ITEM],
    )

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is True
    assert "projects" in resp.data
    assert len(resp.data["projects"]) == 1
    assert resp.data["projects"][0]["name"] == "Project Alpha"


def test_list_projects_no_org():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    # User with no org_id
    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET single project
# ---------------------------------------------------------------------------

def test_get_project_success():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        projects_items=[SAMPLE_PROJECT_ITEM],
    )

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "project_id": "proj-1"}))

    assert resp.success is True
    assert resp.data["project"]["id"] == "proj-1"


def test_get_project_not_found():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM, projects_items=[])
    mock_db.projects.get_by_key.return_value = None

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "project_id": "nonexistent"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# CREATE project
# ---------------------------------------------------------------------------

def test_create_project_success():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({
        "action": "create",
        "name": "New Project",
        "projectType": "ai_report",
    }))

    assert resp.success is True
    assert resp.status_code == 201
    assert resp.data["project"]["name"] == "New Project"
    mock_db.projects.create.assert_called_once()


def test_create_project_no_org():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "create", "name": "Orphan"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# UPDATE project
# ---------------------------------------------------------------------------

def test_update_project_success():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({
        "action": "update",
        "project_id": "proj-1",
        "name": "Renamed Project",
    }))

    assert resp.success is True
    mock_db.projects.raw_update_item.assert_called_once()


def test_update_project_no_fields():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({
        "action": "update",
        "project_id": "proj-1",
    }))

    assert resp.success is False
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# DELETE project
# ---------------------------------------------------------------------------

def test_delete_project_success():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.delete(make_request({"action": "delete", "project_id": "proj-1"}))

    assert resp.success is True
    mock_db.projects.delete_by_key.assert_called_once()


# ---------------------------------------------------------------------------
# Invalid action
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = MagicMock()

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    from managers.projects.ProjectResourceManager import ProjectResourceManager

    mock_db = MagicMock()

    mgr = ProjectResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
