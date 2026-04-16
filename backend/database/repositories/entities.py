"""Single source of truth for entity registration.

Each entity references its schema dataclass (from database/schemas/) and adds
DB-specific metadata. Connectors introspect the schema to derive field names,
types, and defaults — no duplication.

SQLAlchemyConnector: builds ORM models from schema fields + entity metadata
DynamoDBConnector: derives table name map from dynamo_suffix
"""
from dataclasses import dataclass, field
from typing import Type, List

from database.schemas.user import UserItem
from database.schemas.user_role import UserRoleItem
from database.schemas.organization import OrganizationItem
from database.schemas.org_invitation import OrgInvitationItem
from database.schemas.project import ProjectItem
from database.schemas.notification import NotificationItem
from database.schemas.ai_chat_session import AIChatSessionItem
from database.schemas.ai_chat_message import AIChatMessageItem
from database.schemas.audit_log import AuditLogItem
from database.schemas.report import ReportItem
from database.schemas.report_job import ReportJobItem
from database.schemas.dataset import DatasetItem
from database.schemas.model_config import ModelConfigItem
from database.schemas.report_cache import ReportCacheItem


@dataclass
class ConfigItem:
    """Minimal schema for the config table (no dedicated schema file)."""
    pk: str = ""
    sk: str = ""
    data: str = ""
    updated_at: str = ""


@dataclass
class Entity:
    schema: Type
    dynamo_suffix: str
    pk: List[str]
    indexes: List[str] = field(default_factory=list)
    unique: List[str] = field(default_factory=list)
    text_fields: List[str] = field(default_factory=list)
    non_nullable: List[str] = field(default_factory=list)


ENTITIES = {
    "users": Entity(
        schema=UserItem,
        dynamo_suffix="users",
        pk=["id"],
        indexes=["email", "org_id"],
        unique=["email"],
        text_fields=["avatar_url", "notification_preferences", "oauth_providers"],
        non_nullable=["email"],
    ),
    "user_roles": Entity(
        schema=UserRoleItem,
        dynamo_suffix="user-roles",
        pk=["user_id", "org_role"],
        indexes=["org_id"],
        non_nullable=["org_id", "role"],
    ),
    "config": Entity(
        schema=ConfigItem,
        dynamo_suffix="config",
        pk=["pk", "sk"],
        text_fields=["data"],
    ),
    "organizations": Entity(
        schema=OrganizationItem,
        dynamo_suffix="organizations",
        pk=["id"],
        text_fields=["logo_url", "settings"],
        non_nullable=["name", "slug", "owner_id"],
    ),
    "org_invitations": Entity(
        schema=OrgInvitationItem,
        dynamo_suffix="org-invitations",
        pk=["id"],
        indexes=["org_id", "token"],
        unique=["token"],
        non_nullable=["org_id", "email", "token", "invited_by"],
    ),
    "projects": Entity(
        schema=ProjectItem,
        dynamo_suffix="projects",
        pk=["org_id", "id"],
        indexes=[],
        text_fields=["description"],
        non_nullable=["org_id", "name"],
    ),
    "notifications": Entity(
        schema=NotificationItem,
        dynamo_suffix="notifications",
        pk=["user_id", "timestamp_id"],
        text_fields=["message", "action_url", "metadata"],
    ),
    "ai_chat_sessions": Entity(
        schema=AIChatSessionItem,
        dynamo_suffix="ai-chat-sessions",
        pk=["user_id", "id"],
        indexes=[],
        non_nullable=["user_id", "org_id"],
    ),
    "ai_chat_messages": Entity(
        schema=AIChatMessageItem,
        dynamo_suffix="ai-chat-messages",
        pk=["session_id", "timestamp_id"],
        text_fields=["content", "tool_calls", "chart_config"],
    ),
    "audit_log": Entity(
        schema=AuditLogItem,
        dynamo_suffix="audit-log",
        pk=["id", "timestamp"],
        indexes=["user_id", "org_id"],
        text_fields=["details"],
        non_nullable=["user_id", "action"],
    ),
    "reports": Entity(
        schema=ReportItem,
        dynamo_suffix="reports",
        pk=["org_id", "id"],
        indexes=["project_id"],
        text_fields=["dataset_config", "report_config"],
        non_nullable=["org_id", "name"],
    ),
    "report_jobs": Entity(
        schema=ReportJobItem,
        dynamo_suffix="report-jobs",
        pk=["org_id", "id"],
        indexes=["report_id", "status"],
        text_fields=["result_data"],
        non_nullable=["org_id", "report_id"],
    ),
    "datasets": Entity(
        schema=DatasetItem,
        dynamo_suffix="datasets",
        pk=["org_id", "id"],
        text_fields=["domain_data"],
        non_nullable=["org_id", "name"],
    ),
    "model_configs": Entity(
        schema=ModelConfigItem,
        dynamo_suffix="model-configs",
        pk=["org_id", "id"],
        text_fields=["model_config"],
        non_nullable=["org_id", "name"],
    ),
    "report_cache": Entity(
        schema=ReportCacheItem,
        dynamo_suffix="report-cache",
        pk=["report_id", "cache_key"],
        text_fields=["cache_data"],
    ),
}
