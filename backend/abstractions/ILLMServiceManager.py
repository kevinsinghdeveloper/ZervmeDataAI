from abc import abstractmethod
from abstractions.IServiceManagerBase import IServiceManagerBase


class ILLMServiceManager(IServiceManagerBase):
    def __init__(self, config=None):
        super().__init__(config)

    @abstractmethod
    def run_task(self, request_resource_model):
        pass

    @abstractmethod
    def get_base_prompt(self, prompt, llm_instructions):
        pass
