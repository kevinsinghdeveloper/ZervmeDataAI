"""Specialized repository interface for time entries."""
from abc import abstractmethod
from typing import List
from abstractions.IRepository import IRepository
from database.schemas.time_entry import TimeEntryItem


class ITimeEntryRepository(IRepository):

    @abstractmethod
    def find_by_user_date_range(self, user_id: str, start_date: str, end_date: str) -> List[TimeEntryItem]:
        pass

    @abstractmethod
    def find_running_timer(self, user_id: str) -> List[dict]:
        pass

    @abstractmethod
    def find_by_project_date(self, project_id: str) -> List[TimeEntryItem]:
        pass

    @abstractmethod
    def batch_create(self, items: List[TimeEntryItem]) -> int:
        pass

    @abstractmethod
    def count_by_project(self, org_id: str, project_id: str) -> int:
        pass
