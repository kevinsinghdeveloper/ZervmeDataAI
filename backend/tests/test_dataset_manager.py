"""Unit tests for DatasetResourceManager."""
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

SAMPLE_DATASET_ITEM = {
    "org_id": "org-456",
    "id": "ds-1",
    "name": "Customer Feedback",
    "description": "Aggregated customer feedback dataset",
    "domain_data": '{"schema": "feedback_v2"}',
    "data_source": "s3://bucket/feedback/",
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_DATASET_ITEM_2 = {
    "org_id": "org-456",
    "id": "ds-2",
    "name": "Sales Data",
    "description": "Monthly sales figures",
    "data_source": "s3://bucket/sales/",
    "status": "archived",
    "created_at": "2024-02-01T00:00:00",
    "updated_at": "2024-02-01T00:00:00",
}


def _build_mock_db(users_item=None, datasets_items=None):
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

    # datasets repo
    mock_db.datasets.list_all.return_value = datasets_items or []
    mock_db.datasets.get_by_key.return_value = (
        datasets_items[0] if datasets_items else None
    )
    mock_db.datasets.create.return_value = {}
    mock_db.datasets.raw_update_item.return_value = {}
    mock_db.datasets.delete_by_key.return_value = {}

    return mock_db


# ---------------------------------------------------------------------------
# LIST datasets
# ---------------------------------------------------------------------------

def test_list_datasets_success():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        datasets_items=[SAMPLE_DATASET_ITEM, SAMPLE_DATASET_ITEM_2],
    )

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is True
    assert "datasets" in resp.data
    assert len(resp.data["datasets"]) == 2
    assert resp.data["datasets"][0]["name"] == "Customer Feedback"
    assert resp.data["datasets"][1]["name"] == "Sales Data"
    mock_db.datasets.list_all.assert_called_once_with(org_id="org-456")


def test_list_datasets_filtered_by_status():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        datasets_items=[SAMPLE_DATASET_ITEM, SAMPLE_DATASET_ITEM_2],
    )

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list", "status": "archived"}))

    assert resp.success is True
    assert len(resp.data["datasets"]) == 1
    assert resp.data["datasets"][0]["status"] == "archived"


def test_list_datasets_no_org():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET single dataset
# ---------------------------------------------------------------------------

def test_get_dataset_success():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        datasets_items=[SAMPLE_DATASET_ITEM],
    )

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "dataset_id": "ds-1"}))

    assert resp.success is True
    assert resp.data["dataset"]["id"] == "ds-1"
    assert resp.data["dataset"]["name"] == "Customer Feedback"
    mock_db.datasets.get_by_key.assert_called_once_with(
        {"org_id": "org-456", "id": "ds-1"}
    )


def test_get_dataset_not_found():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM, datasets_items=[])
    mock_db.datasets.get_by_key.return_value = None

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "dataset_id": "nonexistent"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# CREATE dataset
# ---------------------------------------------------------------------------

def test_create_dataset_success():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({
        "action": "create",
        "name": "New Dataset",
        "description": "A fresh dataset",
        "domainData": {"schema": "v3"},
        "dataSource": "s3://bucket/new/",
    }))

    assert resp.success is True
    assert resp.status_code == 201
    assert resp.data["dataset"]["name"] == "New Dataset"
    assert resp.data["dataset"]["description"] == "A fresh dataset"
    mock_db.datasets.create.assert_called_once()

    # Verify the item dict passed to create has the right org_id
    created_item = mock_db.datasets.create.call_args[0][0]
    assert created_item["org_id"] == "org-456"
    assert created_item["name"] == "New Dataset"


def test_create_dataset_no_org():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "create", "name": "Orphan"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE dataset
# ---------------------------------------------------------------------------

def test_delete_dataset_success():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.delete(make_request({"action": "delete", "dataset_id": "ds-1"}))

    assert resp.success is True
    mock_db.datasets.delete_by_key.assert_called_once_with(
        {"org_id": "org-456", "id": "ds-1"}
    )


# ---------------------------------------------------------------------------
# Invalid action
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = MagicMock()

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    from managers.datasets.DatasetResourceManager import DatasetResourceManager

    mock_db = MagicMock()

    mgr = DatasetResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
