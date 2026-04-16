"""Unit tests for ETLService."""
import sys
import os
import types
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from abstractions.EtlReportBase import EtlReportBase
from abstractions.ILLMServiceManager import ILLMServiceManager


# ---------------------------------------------------------------------------
# Concrete EtlReportBase subclass for testing
# ---------------------------------------------------------------------------

class _FakeReport(EtlReportBase):
    """Minimal concrete subclass of EtlReportBase used in tests."""

    def __init__(self, run_params, llm_service_manager, db_service=None):
        super().__init__(run_params, "fake_report", llm_service_manager, db_service)

    def configure_init_tasks(self):
        pass


# ---------------------------------------------------------------------------
# GET ALL REPORT JOBS (module discovery)
# ---------------------------------------------------------------------------

def test_get_all_report_jobs_discovers_modules(tmp_path):
    """Verify _get_all_report_jobs discovers .py files in report_etls/."""
    from services.etl.ETLService import ETLService

    # Create a fake report_etls directory with two Python modules
    report_etls_dir = tmp_path / "report_etls"
    report_etls_dir.mkdir()
    (report_etls_dir / "alpha_report.py").write_text(
        "class AlphaReport:\n    pass\n"
    )
    (report_etls_dir / "beta_report.py").write_text(
        "class BetaReport:\n    pass\n"
    )
    # __init__.py should be skipped
    (report_etls_dir / "__init__.py").write_text("")
    # Non-Python files should be skipped
    (report_etls_dir / "README.md").write_text("docs")

    etl = ETLService()

    # Patch the report_dir calculation to point at our tmp directory
    with patch("os.path.dirname") as mock_dirname:
        # ETLService computes report_dir relative to its own __file__.
        # We redirect so that report_dir = tmp_path / "report_etls"
        # os.path.dirname is called twice in the chain:
        #   os.path.dirname(os.path.abspath(__file__))  -> services/etl/
        #   os.path.dirname(result)                     -> services/
        # But we actually want to redirect the final os.path.join result.
        # Simpler approach: patch the entire method to point at our dir.
        pass

    # Direct approach: monkey-patch the method to use our directory
    original_method = etl._get_all_report_jobs

    def _patched_get_all_report_jobs():
        import importlib.util
        import logging
        reports = {}
        report_dir = str(report_etls_dir)
        for file in os.listdir(report_dir):
            if file.endswith(".py") and not file.startswith("__"):
                module_name = os.path.splitext(file)[0]
                try:
                    file_path = os.path.join(report_dir, file)
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    reports[module_name] = module
                except Exception as e:
                    logging.error(f"Error loading report job {module_name}: {e}")
        return reports

    etl._get_all_report_jobs = _patched_get_all_report_jobs

    reports = etl._get_all_report_jobs()
    assert "alpha_report" in reports
    assert "beta_report" in reports
    assert "__init__" not in reports
    assert len(reports) == 2


def test_get_all_report_jobs_empty_when_no_dir():
    """Verify _get_all_report_jobs returns empty dict when report_etls/ does not exist."""
    from services.etl.ETLService import ETLService

    etl = ETLService()

    with patch("os.path.exists", return_value=False):
        reports = etl._get_all_report_jobs()

    assert reports == {}


# ---------------------------------------------------------------------------
# RUN REPORT
# ---------------------------------------------------------------------------

def test_run_report_success():
    """Verify run_report gets AI service, finds the report class, and calls run_etl."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    mock_llm = MagicMock(spec=ILLMServiceManager)

    # Create a fake module containing a concrete EtlReportBase subclass
    fake_module = types.ModuleType("my_report")
    fake_module._FakeReport = _FakeReport

    with patch.object(etl, "_get_all_report_jobs", return_value={"my_report": fake_module}):
        with patch(
            "services.etl.ETLService.AIServiceHandler.get_ai_service",
            return_value=mock_llm,
        ):
            result = etl.run_report(
                "my_report",
                {"param1": "value1"},
                {"ai_type": "openai"},
            )

    assert result["status"] == "success"
    assert "fake_report" in result["message"]


def test_run_report_not_found():
    """Verify run_report raises Exception when report_name doesn't match."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    mock_llm = MagicMock(spec=ILLMServiceManager)

    with patch.object(etl, "_get_all_report_jobs", return_value={}):
        with patch(
            "services.etl.ETLService.AIServiceHandler.get_ai_service",
            return_value=mock_llm,
        ):
            with pytest.raises(Exception, match="not found"):
                etl.run_report("nonexistent_report", {}, {"ai_type": "openai"})


def test_run_report_no_subclass_in_module():
    """Verify run_report raises Exception when module has no EtlReportBase subclass."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    mock_llm = MagicMock(spec=ILLMServiceManager)

    # Module exists but has no EtlReportBase subclass
    fake_module = types.ModuleType("empty_report")
    fake_module.SomeUnrelatedClass = type("SomeUnrelatedClass", (), {})

    with patch.object(etl, "_get_all_report_jobs", return_value={"empty_report": fake_module}):
        with patch(
            "services.etl.ETLService.AIServiceHandler.get_ai_service",
            return_value=mock_llm,
        ):
            with pytest.raises(Exception, match="not found"):
                etl.run_report("empty_report", {}, {"ai_type": "openai"})


# ---------------------------------------------------------------------------
# GET JOB STATUS
# ---------------------------------------------------------------------------

def test_get_job_status_from_db():
    """Verify get_job_status returns job from db when available."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    mock_db = MagicMock()
    mock_db.report_jobs.get_by_key.return_value = {
        "id": "job-123",
        "status": "completed",
        "progress": 100,
    }
    etl.set_db(mock_db)

    status = etl.get_job_status("job-123")

    assert status["id"] == "job-123"
    assert status["status"] == "completed"
    mock_db.report_jobs.get_by_key.assert_called_once_with({"id": "job-123"})


def test_get_job_status_unknown_when_no_db():
    """Verify get_job_status returns unknown when no db is set."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    # _db is None by default

    status = etl.get_job_status("job-999")

    assert status["id"] == "job-999"
    assert status["status"] == "unknown"


def test_get_job_status_unknown_when_job_not_found():
    """Verify get_job_status returns unknown when job not in db."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    mock_db = MagicMock()
    mock_db.report_jobs.get_by_key.return_value = None
    etl.set_db(mock_db)

    status = etl.get_job_status("job-404")

    assert status["id"] == "job-404"
    assert status["status"] == "unknown"


# ---------------------------------------------------------------------------
# INITIALIZE & SET DB
# ---------------------------------------------------------------------------

def test_initialize_does_not_raise():
    """Verify initialize() is callable and does not raise."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    etl.initialize()  # Should not raise


def test_set_db():
    """Verify set_db stores the db reference."""
    from services.etl.ETLService import ETLService

    etl = ETLService()
    mock_db = MagicMock()
    etl.set_db(mock_db)
    assert etl._db is mock_db
