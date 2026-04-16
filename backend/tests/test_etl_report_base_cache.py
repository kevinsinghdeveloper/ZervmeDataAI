"""Unit tests for EtlReportBase caching (DynamoDB + file fallback)."""
import json
import os
import sys
import pytest
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.EtlReportBase import EtlReportBase
from abstractions.ILLMServiceManager import ILLMServiceManager


# ---------------------------------------------------------------------------
# Concrete subclass for testing
# ---------------------------------------------------------------------------

class _TestReport(EtlReportBase):
    def __init__(self, run_params, llm_service_manager, db_service=None):
        super().__init__(run_params, "test_report", llm_service_manager, db_service)

    def configure_init_tasks(self):
        pass


def _make_report(use_cache=True, db_service=None):
    """Factory for a _TestReport with default mocks."""
    llm = MagicMock(spec=ILLMServiceManager)
    return _TestReport({"use_cache": use_cache}, llm, db_service)


def _make_db_service(report_cache_repo=None):
    """Return a mock DatabaseService with a report_cache repository."""
    db = MagicMock()
    db.report_cache = report_cache_repo if report_cache_repo is not None else MagicMock()
    return db


# ===========================================================================
# _has_db_cache property
# ===========================================================================

class TestHasDbCache:

    def test_true_when_db_and_report_cache_present(self):
        db = _make_db_service()
        report = _make_report(db_service=db)
        assert report._has_db_cache is True

    def test_false_when_no_db(self):
        report = _make_report(db_service=None)
        assert report._has_db_cache is False

    def test_false_when_report_cache_is_none(self):
        db = MagicMock()
        db.report_cache = None
        report = _make_report(db_service=db)
        assert report._has_db_cache is False

    def test_false_when_db_lacks_report_cache_attr(self):
        db = MagicMock(spec=[])  # empty spec -> no attributes
        report = _make_report(db_service=db)
        assert report._has_db_cache is False


# ===========================================================================
# save_cache
# ===========================================================================

class TestSaveCache:

    def test_noop_when_caching_disabled(self):
        db = _make_db_service()
        report = _make_report(use_cache=False, db_service=db)
        report._llm_response_data = {"key": "value"}
        report.save_cache()
        db.report_cache.upsert.assert_not_called()

    def test_writes_to_dynamodb(self):
        mock_repo = MagicMock()
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)
        report._llm_response_data = {"competitors": ["acme"]}

        report.save_cache()

        mock_repo.upsert.assert_called_once()
        saved_item = mock_repo.upsert.call_args[0][0]
        assert saved_item["report_id"] == "test_report"
        assert saved_item["cache_key"] == "full_response"
        parsed = json.loads(saved_item["cache_data"])
        assert parsed == {"competitors": ["acme"]}

    @patch("abstractions.EtlReportBase.EtlReportBase._save_cache_to_file")
    def test_falls_back_to_file_when_no_db(self, mock_file_save):
        report = _make_report(db_service=None)
        report._llm_response_data = {"key": "val"}

        report.save_cache()

        mock_file_save.assert_called_once()
        cache_json = mock_file_save.call_args[0][0]
        assert json.loads(cache_json) == {"key": "val"}

    @patch("abstractions.EtlReportBase.EtlReportBase._save_cache_to_file")
    def test_falls_back_to_file_when_dynamo_raises(self, mock_file_save):
        mock_repo = MagicMock()
        mock_repo.upsert.side_effect = Exception("DynamoDB timeout")
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)
        report._llm_response_data = {"key": "val"}

        report.save_cache()

        mock_file_save.assert_called_once()

    def test_uses_json_serializer_for_custom_objects(self):
        """Objects with to_dict() should be serialized via the custom serializer."""
        mock_repo = MagicMock()
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)

        class FakeObj:
            def to_dict(self):
                return {"serialized": True}

        report._llm_response_data = {"obj": FakeObj()}
        report.save_cache()

        saved_item = mock_repo.upsert.call_args[0][0]
        parsed = json.loads(saved_item["cache_data"])
        assert parsed["obj"] == {"serialized": True}


# ===========================================================================
# load_cache
# ===========================================================================

class TestLoadCache:

    def test_returns_false_when_caching_disabled(self):
        report = _make_report(use_cache=False)
        assert report.load_cache() is False

    def test_loads_from_dynamodb(self):
        cached_data = {"competitors": ["acme", "beta"]}
        mock_repo = MagicMock()
        mock_repo.get_by_key.return_value = {
            "report_id": "test_report",
            "cache_key": "full_response",
            "cache_data": json.dumps(cached_data),
        }
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)

        result = report.load_cache()

        assert result is True
        assert report._llm_response_data == cached_data
        mock_repo.get_by_key.assert_called_once_with({
            "report_id": "test_report",
            "cache_key": "full_response",
        })

    def test_returns_false_when_dynamo_item_missing(self):
        mock_repo = MagicMock()
        mock_repo.get_by_key.return_value = None
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)

        with patch.object(report, "_load_cache_from_file", return_value=False):
            result = report.load_cache()

        assert result is False

    def test_returns_false_when_dynamo_item_has_empty_cache_data(self):
        mock_repo = MagicMock()
        mock_repo.get_by_key.return_value = {
            "report_id": "test_report",
            "cache_key": "full_response",
            "cache_data": None,
        }
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)

        with patch.object(report, "_load_cache_from_file", return_value=False):
            result = report.load_cache()

        assert result is False

    @patch("abstractions.EtlReportBase.EtlReportBase._load_cache_from_file")
    def test_falls_back_to_file_when_no_db(self, mock_file_load):
        mock_file_load.return_value = True
        report = _make_report(db_service=None)
        report._llm_response_data = {}

        result = report.load_cache()

        assert result is True
        mock_file_load.assert_called_once()

    @patch("abstractions.EtlReportBase.EtlReportBase._load_cache_from_file")
    def test_falls_back_to_file_when_dynamo_raises(self, mock_file_load):
        mock_file_load.return_value = True
        mock_repo = MagicMock()
        mock_repo.get_by_key.side_effect = Exception("DynamoDB error")
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)

        result = report.load_cache()

        assert result is True
        mock_file_load.assert_called_once()


# ===========================================================================
# is_cached
# ===========================================================================

class TestIsCached:

    def test_returns_false_when_caching_disabled(self):
        report = _make_report(use_cache=False)
        report._llm_response_data = {"target_company": {}}
        assert report.is_cached("target_company") is False

    def test_returns_true_when_key_in_memory(self):
        report = _make_report()
        report._llm_response_data = {"target_company": {"data": 1}}
        assert report.is_cached("target_company") is True

    def test_returns_false_when_key_not_in_memory(self):
        report = _make_report()
        report._llm_response_data = {"target_company": {"data": 1}}
        assert report.is_cached("nonexistent") is False

    def test_hydrates_from_dynamodb_when_memory_empty(self):
        cached_data = {"target_company": {"data": 1}, "competitors": {}}
        mock_repo = MagicMock()
        mock_repo.get_by_key.return_value = {
            "report_id": "test_report",
            "cache_key": "full_response",
            "cache_data": json.dumps(cached_data),
        }
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)
        # _llm_response_data is empty by default

        assert report.is_cached("target_company") is True
        assert report._llm_response_data == cached_data

    def test_hydrates_from_dynamodb_key_missing(self):
        cached_data = {"target_company": {"data": 1}}
        mock_repo = MagicMock()
        mock_repo.get_by_key.return_value = {
            "report_id": "test_report",
            "cache_key": "full_response",
            "cache_data": json.dumps(cached_data),
        }
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)

        assert report.is_cached("nonexistent_key") is False

    @patch("abstractions.EtlReportBase.EtlReportBase._load_cache_from_file")
    def test_falls_back_to_file_when_no_db_and_memory_empty(self, mock_file_load):
        report = _make_report(db_service=None)

        def _load_side_effect():
            report._llm_response_data = {"target_company": {}}
            return True

        mock_file_load.side_effect = _load_side_effect

        assert report.is_cached("target_company") is True
        mock_file_load.assert_called_once()

    @patch("abstractions.EtlReportBase.EtlReportBase._load_cache_from_file")
    def test_falls_back_to_file_when_dynamo_raises(self, mock_file_load):
        mock_repo = MagicMock()
        mock_repo.get_by_key.side_effect = Exception("DynamoDB error")
        db = _make_db_service(report_cache_repo=mock_repo)
        report = _make_report(db_service=db)

        def _load_side_effect():
            report._llm_response_data = {"target_company": {}}
            return True

        mock_file_load.side_effect = _load_side_effect

        assert report.is_cached("target_company") is True

    @patch("abstractions.EtlReportBase.EtlReportBase._load_cache_from_file", return_value=False)
    def test_returns_false_when_nothing_cached_anywhere(self, mock_file_load):
        report = _make_report(db_service=None)
        assert report.is_cached("anything") is False


# ===========================================================================
# File-based fallback helpers
# ===========================================================================

class TestFileCacheHelpers:

    def test_save_cache_to_file(self, tmp_path):
        report = _make_report()
        cache_file = str(tmp_path / "cache" / "test_report.json")
        report._cache_file = cache_file

        data = {"key": "value"}
        report._save_cache_to_file(json.dumps(data))

        assert os.path.exists(cache_file)
        with open(cache_file, "r") as f:
            assert json.load(f) == data

    def test_load_cache_from_file(self, tmp_path):
        report = _make_report()
        cache_file = str(tmp_path / "test_report.json")
        report._cache_file = cache_file

        data = {"competitors": ["x", "y"]}
        with open(cache_file, "w") as f:
            json.dump(data, f)

        result = report._load_cache_from_file()

        assert result is True
        assert report._llm_response_data == data

    def test_load_cache_from_file_returns_false_when_missing(self, tmp_path):
        report = _make_report()
        report._cache_file = str(tmp_path / "nonexistent.json")
        assert report._load_cache_from_file() is False


# ===========================================================================
# Constructor / backward compatibility
# ===========================================================================

class TestConstructor:

    def test_db_service_defaults_to_none(self):
        llm = MagicMock(spec=ILLMServiceManager)
        report = _TestReport({"use_cache": True}, llm)
        assert report._db is None
        assert report._has_db_cache is False

    def test_db_service_stored(self):
        db = _make_db_service()
        report = _make_report(db_service=db)
        assert report._db is db

    def test_etl_name_stored(self):
        report = _make_report()
        assert report._etl_name == "test_report"

    def test_default_cache_key_constant(self):
        assert EtlReportBase._DEFAULT_CACHE_KEY == "full_response"


# ===========================================================================
# Integration: save then load round-trip through DynamoDB mock
# ===========================================================================

class TestRoundTrip:

    def test_save_then_load_via_dynamodb(self):
        """Simulate a full save + load cycle using an in-memory store."""
        store = {}
        mock_repo = MagicMock()

        def _upsert(item):
            key = (item["report_id"], item["cache_key"])
            store[key] = item

        def _get_by_key(key):
            lookup = (key["report_id"], key["cache_key"])
            return store.get(lookup)

        mock_repo.upsert.side_effect = _upsert
        mock_repo.get_by_key.side_effect = _get_by_key

        db = _make_db_service(report_cache_repo=mock_repo)

        # Save
        report_save = _make_report(db_service=db)
        report_save._llm_response_data = {
            "target_company": {"name": "Acme"},
            "competitors": {"Beta": {}, "Gamma": {}},
        }
        report_save.save_cache()

        # Load in a fresh report instance
        report_load = _make_report(db_service=db)
        assert report_load._llm_response_data == {}

        loaded = report_load.load_cache()
        assert loaded is True
        assert report_load._llm_response_data == {
            "target_company": {"name": "Acme"},
            "competitors": {"Beta": {}, "Gamma": {}},
        }
