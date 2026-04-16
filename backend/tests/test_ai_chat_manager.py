"""Unit tests for AIChatResourceManager."""
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

SAMPLE_SESSION_ITEM = {
    "user_id": "user-123",
    "id": "sess-1",
    "org_id": "org-456",
    "title": "New Chat",
    "message_count": 0,
    "last_message_at": None,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
}

SAMPLE_MESSAGE_ITEM = {
    "session_id": "sess-1",
    "timestamp_id": "2024-01-01T00:00:00#msg-1",
    "role": "user",
    "content": "Hello",
    "chart_config": None,
    "created_at": "2024-01-01T00:00:00",
}


def _build_mock_db(users_item=None, sessions_items=None, messages_items=None):
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

    # ai_chat_sessions repo
    mock_db.ai_chat_sessions.list_all.return_value = sessions_items or []
    mock_db.ai_chat_sessions.get_by_key.return_value = (sessions_items[0] if sessions_items else None)
    mock_db.ai_chat_sessions.create.return_value = {}
    mock_db.ai_chat_sessions.delete_by_key.return_value = {}

    # ai_chat_messages repo
    mock_db.ai_chat_messages.list_all.return_value = messages_items or []
    mock_db.ai_chat_messages.create.return_value = {}

    return mock_db


# ---------------------------------------------------------------------------
# LIST sessions
# ---------------------------------------------------------------------------

def test_list_sessions_success():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        sessions_items=[SAMPLE_SESSION_ITEM],
    )

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_sessions"}))

    assert resp.success is True
    assert "sessions" in resp.data
    assert len(resp.data["sessions"]) == 1
    assert resp.data["sessions"][0]["title"] == "New Chat"


# ---------------------------------------------------------------------------
# CREATE session
# ---------------------------------------------------------------------------

def test_create_session_success():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "create_session", "title": "My Chat"}))

    assert resp.success is True
    assert resp.status_code == 201
    assert "session" in resp.data
    assert resp.data["session"]["title"] == "My Chat"
    mock_db.ai_chat_sessions.create.assert_called_once()


# ---------------------------------------------------------------------------
# GET session
# ---------------------------------------------------------------------------

def test_get_session_success():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        sessions_items=[SAMPLE_SESSION_ITEM],
    )

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get_session", "session_id": "sess-1"}))

    assert resp.success is True
    assert "session" in resp.data
    assert resp.data["session"]["id"] == "sess-1"


def test_get_session_not_found():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM, sessions_items=[])
    mock_db.ai_chat_sessions.get_by_key.return_value = None

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "get_session", "session_id": "nonexistent"}))

    assert resp.success is False
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE session
# ---------------------------------------------------------------------------

def test_delete_session_success():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.delete(make_request({"action": "delete_session", "session_id": "sess-1"}))

    assert resp.success is True
    assert resp.message == "Session deleted"
    mock_db.ai_chat_sessions.delete_by_key.assert_called_once()


# ---------------------------------------------------------------------------
# LIST messages
# ---------------------------------------------------------------------------

def test_list_messages_success():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(
        users_item=SAMPLE_USER_ITEM,
        messages_items=[SAMPLE_MESSAGE_ITEM],
    )

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "list_messages", "session_id": "sess-1"}))

    assert resp.success is True
    assert "messages" in resp.data
    assert len(resp.data["messages"]) == 1
    assert resp.data["messages"][0]["content"] == "Hello"


# ---------------------------------------------------------------------------
# SEND message (with AI service)
# ---------------------------------------------------------------------------

def test_send_message_with_ai():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mock_ai_service = MagicMock()
    mock_ai_service.chat.return_value = {"content": "AI response text", "chart_config": None}

    mgr = AIChatResourceManager(service_managers={"db": mock_db, "ai": mock_ai_service})
    resp = mgr.post(make_request({
        "action": "send_message",
        "session_id": "sess-1",
        "content": "Hello AI",
    }))

    assert resp.success is True
    assert "userMessage" in resp.data
    assert "assistantMessage" in resp.data
    assert resp.data["userMessage"]["content"] == "Hello AI"
    assert resp.data["assistantMessage"]["content"] == "AI response text"
    mock_ai_service.chat.assert_called_once_with(
        "Hello AI", "sess-1", "user-123",
        conversation_history=[], model_id=None,
    )
    assert mock_db.ai_chat_messages.create.call_count == 2


# ---------------------------------------------------------------------------
# SEND message (no AI service)
# ---------------------------------------------------------------------------

def test_send_message_no_ai():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = _build_mock_db(users_item=SAMPLE_USER_ITEM)

    mgr = AIChatResourceManager(service_managers={"db": mock_db})  # no ai service
    resp = mgr.post(make_request({
        "action": "send_message",
        "session_id": "sess-1",
        "content": "Hello",
    }))

    assert resp.success is True
    assert "userMessage" in resp.data
    assert resp.data["assistantMessage"]["content"] == "AI service unavailable"
    assert resp.data["assistantMessage"]["role"] == "assistant"
    # Only one create call for the user message (no assistant message saved)
    mock_db.ai_chat_messages.create.assert_called_once()


# ---------------------------------------------------------------------------
# SUGGEST entry
# ---------------------------------------------------------------------------

def test_suggest_entry_success():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = MagicMock()

    mock_ai_service = MagicMock()
    mock_ai_service.suggest_time_entry.return_value = {"project": "proj-1", "hours": 2}

    mgr = AIChatResourceManager(service_managers={"db": mock_db, "ai": mock_ai_service})
    resp = mgr.post(make_request({"action": "suggest_entry", "description": "worked on UI"}))

    assert resp.success is True
    assert "suggestion" in resp.data
    assert resp.data["suggestion"]["project"] == "proj-1"
    mock_ai_service.suggest_time_entry.assert_called_once()


def test_suggest_entry_no_service():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = MagicMock()

    mgr = AIChatResourceManager(service_managers={"db": mock_db})  # no ai service
    resp = mgr.post(make_request({"action": "suggest_entry"}))

    assert resp.success is False
    assert resp.status_code == 503
    assert "AI service unavailable" in resp.error


# ---------------------------------------------------------------------------
# CATEGORIZE
# ---------------------------------------------------------------------------

def test_categorize_success():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = MagicMock()

    mock_ai_service = MagicMock()
    mock_ai_service.categorize_entry.return_value = {"category": "development", "confidence": 0.95}

    mgr = AIChatResourceManager(service_managers={"db": mock_db, "ai": mock_ai_service})
    resp = mgr.post(make_request({
        "action": "categorize",
        "description": "Fixed bug in login flow",
        "projects": [{"id": "proj-1", "name": "Frontend"}],
    }))

    assert resp.success is True
    assert "categorization" in resp.data
    assert resp.data["categorization"]["category"] == "development"
    mock_ai_service.categorize_entry.assert_called_once_with(
        "Fixed bug in login flow",
        [{"id": "proj-1", "name": "Frontend"}],
    )


def test_categorize_no_service():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = MagicMock()

    mgr = AIChatResourceManager(service_managers={"db": mock_db})  # no ai service
    resp = mgr.post(make_request({"action": "categorize", "description": "test"}))

    assert resp.success is False
    assert resp.status_code == 503
    assert "AI service unavailable" in resp.error


# ---------------------------------------------------------------------------
# PUT not implemented
# ---------------------------------------------------------------------------

def test_put_not_implemented():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = MagicMock()

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.put(make_request({"action": "update"}))

    assert resp.success is False
    assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Invalid actions
# ---------------------------------------------------------------------------

def test_get_invalid_action():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = MagicMock()

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.get(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400


def test_post_invalid_action():
    from managers.ai_chat.AIChatResourceManager import AIChatResourceManager

    mock_db = MagicMock()

    mgr = AIChatResourceManager(service_managers={"db": mock_db})
    resp = mgr.post(make_request({"action": "nonexistent_action"}))

    assert resp.success is False
    assert resp.status_code == 400
