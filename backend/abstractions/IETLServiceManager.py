from abc import abstractmethod
from abstractions.IServiceManagerBase import IServiceManagerBase


class IETLServiceManager(IServiceManagerBase):
    def __init__(self, config=None):
        super().__init__(config)

    @abstractmethod
    def run_task(self, request):
        pass
