"""Specialized repository interface for timesheets."""
from abc import abstractmethod
from typing import List, Optional
from abstractions.IRepository import IRepository
from database.schemas.timesheet import TimesheetItem


class ITimesheetRepository(IRepository):

    @abstractmethod
    def find_by_org_user_week(self, org_id: str, user_id: str, week_start: str) -> Optional[TimesheetItem]:
        pass

    @abstractmethod
    def find_by_user(self, org_id: str, user_id: str) -> List[TimesheetItem]:
        pass

    @abstractmethod
    def find_by_org_status(self, org_id: str, status: str) -> List[TimesheetItem]:
        pass
