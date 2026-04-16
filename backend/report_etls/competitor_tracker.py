from abstractions.EtlReportBase import EtlReportBase
from abstractions.ILLMServiceManager import ILLMServiceManager


class CompetitorTracker(EtlReportBase):
    def __init__(self, run_params: dict, llm_service_manager: ILLMServiceManager,
                 db_service=None):
        super().__init__(run_params, "competitor_tracker", llm_service_manager, db_service)

    def configure_init_tasks(self):
        self._pre_validation_pipeline_tasks = {
            "Check run params": self.__check_run_params
        }

    def __check_run_params(self):
        pass
