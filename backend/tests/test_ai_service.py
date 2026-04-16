"""Unit tests for AIService (DB-related methods)."""
import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.ai.AIService import AIService


def _build_service():
    mock_db = MagicMock()
    svc = AIService()
    svc.set_db(mock_db)
    return svc, mock_db


class TestAIServiceLoadConfig:
    def test_loads_model_overrides_from_db(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.side_effect = lambda pk, sk: {
            "ai_models": {"data": json.dumps({"models": {"custom-1": {"provider": "openai", "model_name": "gpt-4"}}})},
            "settings": {"data": json.dumps({"chatbotSystemPrompt": "Custom prompt", "defaultModel": "custom-1", "maxConversationHistory": "5"})},
        }.get(sk)

        svc._load_config_from_db()
        assert "custom-1" in svc._model_configs
        assert svc._system_prompt == "Custom prompt"
        assert svc._default_model == "custom-1"
        assert svc._max_conversation_history == 5

    def test_handles_missing_config(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.return_value = None

        svc._load_config_from_db()
        assert svc._model_configs == {}

    def test_handles_db_error_gracefully(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.side_effect = Exception("DB down")

        svc._load_config_from_db()  # Should not raise
        assert svc._model_configs == {}

    def test_no_db_skips_load(self):
        svc = AIService()
        svc._load_config_from_db()  # _db is None, should not raise


class TestAIServiceUpdateModelConfig:
    def test_saves_new_model(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.return_value = None

        result = svc.update_model_config("new-model", {
            "name": "New Model",
            "provider": "anthropic",
            "model_name": "claude-opus-4-6",
        })
        assert result["success"] is True
        mock_db.config.put_config.assert_called_once()
        call_args = mock_db.config.put_config.call_args
        assert call_args[0][0] == "CONFIG"
        assert call_args[0][1] == "ai_models"
        assert "new-model" in call_args[0][2]["models"]

    def test_updates_existing_model(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.return_value = {
            "data": json.dumps({"models": {"m1": {"name": "Old", "provider": "openai"}}})
        }

        result = svc.update_model_config("m1", {"name": "Updated"})
        assert result["success"] is True
        call_data = mock_db.config.put_config.call_args[0][2]
        assert call_data["models"]["m1"]["name"] == "Updated"
        assert call_data["models"]["m1"]["provider"] == "openai"  # preserved

    def test_sets_default_model(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.return_value = None

        svc.update_model_config("m1", {"name": "Test", "isDefault": True})
        assert svc._default_model == "m1"


class TestAIServiceDeleteModelConfig:
    def test_deletes_model(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.return_value = {
            "data": json.dumps({"models": {"m1": {"name": "Model1"}, "m2": {"name": "Model2"}}})
        }

        result = svc.delete_model_config("m1")
        assert result["success"] is True
        call_data = mock_db.config.put_config.call_args[0][2]
        assert "m1" not in call_data["models"]
        assert "m2" in call_data["models"]

    def test_delete_nonexistent_model(self):
        svc, mock_db = _build_service()
        mock_db.config.get_config.return_value = {
            "data": json.dumps({"models": {}})
        }

        result = svc.delete_model_config("nonexistent")
        assert result["success"] is True
        mock_db.config.put_config.assert_not_called()


class TestAIServiceChat:
    def test_missing_api_key_returns_error(self):
        svc, _ = _build_service()
        result = svc.chat("hello", "session-1", "user-1")
        assert "No API key" in result["content"]

    def test_unknown_model_returns_error(self):
        svc, _ = _build_service()
        result = svc.chat("hello", "session-1", "user-1", model_id="nonexistent-model")
        assert "not found" in result["content"]
