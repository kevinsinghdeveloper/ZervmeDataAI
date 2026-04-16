"""Unit tests for ModelConfigResourceManager."""
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

SAMPLE_MODEL_CONFIG_ITEM = {
    "org_id": "org-456",
    "id": "mc-1",
    "name": "GPT-4 Default",
    "model_type_id": "openai-gpt4",
    "model_config": '{"temperature": 0.7, "max_tokens": 2048}',
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_MODEL_CONFIG_ITEM_2 = {
    "org_id": "org-456",
    "id": "mc-2",
    "name": "Claude Sonnet",
    "model_type_id": "anthropic-sonnet",
    "model_config": '{"temperature": 0.5}',
    "status": "inactive",
    "created_at": "2024-02-01T00:00:00",
    "updated_at": "2024-02-01T00:00:00",
}


def _build_mock_db(users_item=None, model_configs_items=None):
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

    # model_configs repo
    mock_db.model_configs.list_all.return_value = model_configs_items or []
    mock_db.model_configs.get_by_key.return_value = (
        model_configs_items[0] if model_configs_items else None
    )
    mock_db.model_configs.create.return_value = {}
    mock_db.model_configs.raw_update_item.return_value = {}
    mock_db.model_configs.delete_by_key.return_value = {}

    return mock_db


# ---------------------------------------------------------------------------
# LIST model configs
# ---------------------------------------------------------------------------

def test_list_model_configs_success():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        model_configs_items=[SAMPLE_MODEL_CONFIG_ITEM, SAMPLE_MODEL_CONFIG_ITEM_2],
    )

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is True
    assert "modelConfigs" in resp.data
    assert len(resp.data["modelConfigs"]) == 2
    assert resp.data["modelConfigs"][0]["name"] == "GPT-4 Default"
    assert resp.data["modelConfigs"][1]["name"] == "Claude Sonnet"
    mock_db.model_configs.list_all.assert_called_once_with(org_id="org-456")


def test_list_model_configs_filtered_by_status():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        model_configs_items=[SAMPLE_MODEL_CONFIG_ITEM, SAMPLE_MODEL_CONFIG_ITEM_2],
    )

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list", "status": "inactive"}))

    assert resp.success is True
    assert len(resp.data["modelConfigs"]) == 1
    assert resp.data["modelConfigs"][0]["status"] == "inactive"


def test_list_model_configs_no_org():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET single model config
# ---------------------------------------------------------------------------

def test_get_model_config_success():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        model_configs_items=[SAMPLE_MODEL_CONFIG_ITEM],
    )

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "config_id": "mc-1"}))

    assert resp.success is True
    assert resp.data["modelConfig"]["id"] == "mc-1"
    assert resp.data["modelConfig"]["name"] == "GPT-4 Default"
    # Verify JSON config was parsed from string
    assert resp.data["modelConfig"]["modelConfig"]["temperature"] == 0.7
    mock_db.model_configs.get_by_key.assert_called_once_with(
        {"org_id": "org-456", "id": "mc-1"}
    )


def test_get_model_config_not_found():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM, model_configs_items=[])
    mock_db.model_configs.get_by_key.return_value = None

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get", "config_id": "nonexistent"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# CREATE model config
# ---------------------------------------------------------------------------

def test_create_model_config_success():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({
        "action": "create",
        "name": "New Model Config",
        "modelTypeId": "openai-gpt4o",
        "modelConfig": {"temperature": 0.9, "max_tokens": 4096},
    }))

    assert resp.success is True
    assert resp.status_code == 201
    assert resp.data["modelConfig"]["name"] == "New Model Config"
    assert resp.data["modelConfig"]["modelTypeId"] == "openai-gpt4o"
    mock_db.model_configs.create.assert_called_once()

    # Verify the item dict passed to create has the right org_id
    created_item = mock_db.model_configs.create.call_args[0][0]
    assert created_item["org_id"] == "org-456"
    assert created_item["name"] == "New Model Config"


def test_create_model_config_no_org():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    user_obj = MagicMock()
    user_obj.org_id = None
    mock_db = MagicMock()
    mock_db.users.get_by_id.return_value = user_obj

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "create", "name": "Orphan Config"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE model config
# ---------------------------------------------------------------------------

def test_delete_model_config_success():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.delete(make_request({"action": "delete", "config_id": "mc-1"}))

    assert resp.success is True
    mock_db.model_configs.delete_by_key.assert_called_once_with(
        {"org_id": "org-456", "id": "mc-1"}
    )


# ---------------------------------------------------------------------------
# Invalid action
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = MagicMock()

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    from managers.model_configs.ModelConfigResourceManager import ModelConfigResourceManager

    mock_db = MagicMock()

    mgr = ModelConfigResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
