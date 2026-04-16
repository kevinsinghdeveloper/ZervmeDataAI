import inspect
import os
import importlib.util
import logging

from abstractions.IServiceManagerBase import IServiceManagerBase
from abstractions.EtlReportBase import EtlReportBase
from abstractions.ILLMServiceManager import ILLMServiceManager
from services.ai.AIServiceHandler import AIServiceHandler
from models.request.ReportProcessorRequestResourceModel import ReportProcessorRequestResourceModel


class ETLService(IServiceManagerBase):
    def __init__(self, config=None):
        super().__init__(config)
        self._db = None

    def set_db(self, db_service):
        self._db = db_service

    def initialize(self):
        pass

    def _get_all_report_jobs(self):
        reports = {}
        report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report_etls")
        if not os.path.exists(report_dir):
            return reports
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

    def _get_report_instance(self, report_name: str, run_params: dict, llm_manager: ILLMServiceManager):
        reports = self._get_all_report_jobs()
        module = reports.get(report_name)
        if not module:
            return None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (inspect.isclass(attr) and issubclass(attr, EtlReportBase) and attr is not EtlReportBase):
                return attr(run_params, llm_manager, self._db)
        return None

    def run_report(self, report_name: str, run_params: dict, llm_config: dict):
        llm_manager = AIServiceHandler.get_ai_service(llm_config)
        etl_report = self._get_report_instance(report_name, run_params, llm_manager)
        if not etl_report:
            raise Exception(f"Report '{report_name}' not found or no EtlReportBase subclass.")
        return etl_report.run_etl()

    def get_job_status(self, job_id: str):
        if self._db and hasattr(self._db, 'report_jobs'):
            job = self._db.report_jobs.get_by_key({"id": job_id})
            if job:
                return job
        return {"id": job_id, "status": "unknown"}
