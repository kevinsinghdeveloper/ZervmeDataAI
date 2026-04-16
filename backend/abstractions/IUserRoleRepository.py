"""Specialized repository interface for user roles."""
from abc import abstractmethod
from typing import List, Optional
from abstractions.IRepository import IRepository
from database.schemas.user_role import UserRoleItem


class IUserRoleRepository(IRepository):

    @abstractmethod
    def get_roles_for_user(self, user_id: str) -> List[UserRoleItem]:
        pass

    @abstractmethod
    def get_user_org_roles(self, user_id: str, org_id: str) -> List[UserRoleItem]:
        pass

    @abstractmethod
    def get_org_members(self, org_id: str) -> List[UserRoleItem]:
        pass

    @abstractmethod
    def get_org_member_ids(self, org_id: str) -> List[str]:
        pass

    @abstractmethod
    def is_super_admin(self, user_id: str) -> bool:
        pass

    @abstractmethod
    def grant_role(self, user_id: str, org_id: str, role: str,
                   granted_by: Optional[str] = None) -> UserRoleItem:
        pass

    @abstractmethod
    def revoke_role(self, user_id: str, org_id: str, role: str) -> None:
        pass

    @abstractmethod
    def revoke_all_org_roles(self, user_id: str, org_id: str) -> None:
        pass

    @abstractmethod
    def is_last_owner(self, org_id: str) -> bool:
        pass
