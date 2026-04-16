"""DatabaseService — reads DB_TYPE and provides typed repository accessors.

Usage in managers:
    db = self._service_managers["db"]
    user = db.users.get_by_id("user-123")
"""
import os
from typing import Optional, Dict

from abstractions.IServiceManagerBase import IServiceManagerBase
from database.repositories.user_repository import UserRepository
from database.repositories.user_role_repository import UserRoleRepository
from database.repositories.config_repository import ConfigRepository


class DatabaseService(IServiceManagerBase):

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self._db_type = os.getenv("DB_TYPE", "dynamodb")

        # Repositories (set during initialize)
        self.users = None
        self.user_roles = None
        self.organizations = None
        self.org_invitations = None
        self.projects = None
        self.notifications = None
        self.ai_chat_sessions = None
        self.ai_chat_messages = None
        self.audit_logs = None
        self.config = None
        self.reports = None
        self.report_jobs = None
        self.datasets = None
        self.model_configs = None
        self.report_cache = None

    def initialize(self):
        if self._db_type == "dynamodb":
            self._init_dynamodb()
        elif self._db_type == "postgres":
            self._init_postgres()
        else:
            raise ValueError(f"Unsupported DB_TYPE: {self._db_type}. Use 'dynamodb' or 'postgres'.")

    def _init_dynamodb(self):
        from database.repositories.connectors.DynamoDBConnector import DynamoDBConnector

        connector = DynamoDBConnector()
        connector.initialize()

        # Specialized repos
        self.users = UserRepository(connector.get_repository("users"))
        self.user_roles = UserRoleRepository(connector.get_repository("user_roles", pk_field="user_id"))
        self.config = ConfigRepository(connector.get_repository("config", pk_field="pk"))

        # Generic repos
        self.organizations = connector.get_repository("organizations")
        self.org_invitations = connector.get_repository("org_invitations")
        self.projects = connector.get_repository("projects", pk_field="org_id")
        self.notifications = connector.get_repository("notifications", pk_field="user_id")
        self.ai_chat_sessions = connector.get_repository("ai_chat_sessions", pk_field="user_id")
        self.ai_chat_messages = connector.get_repository("ai_chat_messages", pk_field="session_id")
        self.audit_logs = connector.get_repository("audit_log")
        self.reports = connector.get_repository("reports", pk_field="org_id")
        self.report_jobs = connector.get_repository("report_jobs", pk_field="org_id")
        self.datasets = connector.get_repository("datasets", pk_field="org_id")
        self.model_configs = connector.get_repository("model_configs", pk_field="org_id")
        self.report_cache = connector.get_repository("report_cache", pk_field="report_id")

    def _init_postgres(self):
        from database.repositories.connectors.SQLAlchemyConnector import SQLAlchemyConnector

        connector = SQLAlchemyConnector()
        connector.initialize()

        # Specialized repos
        self.users = UserRepository(connector.get_repository("users"))
        self.user_roles = UserRoleRepository(connector.get_repository("user_roles", pk_field="user_id"))
        self.config = ConfigRepository(connector.get_repository("config", pk_field="pk"))

        # Generic repos
        self.organizations = connector.get_repository("organizations")
        self.org_invitations = connector.get_repository("org_invitations")
        self.projects = connector.get_repository("projects")
        self.notifications = connector.get_repository("notifications", pk_field="user_id")
        self.ai_chat_sessions = connector.get_repository("ai_chat_sessions")
        self.ai_chat_messages = connector.get_repository("ai_chat_messages", pk_field="session_id")
        self.audit_logs = connector.get_repository("audit_log")
        self.reports = connector.get_repository("reports")
        self.report_jobs = connector.get_repository("report_jobs")
        self.datasets = connector.get_repository("datasets")
        self.model_configs = connector.get_repository("model_configs")
        self.report_cache = connector.get_repository("report_cache")
