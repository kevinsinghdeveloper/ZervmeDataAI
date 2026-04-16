from enum import Enum


class OrgRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"


class OrgPlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class TimeEntrySource(str, Enum):
    MANUAL = "manual"
    TIMER = "timer"
    IMPORT = "import"
    AI_SUGGEST = "ai_suggest"


class ApprovalStatus(str, Enum):
    UNSUBMITTED = "unsubmitted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TimesheetStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class NotificationType(str, Enum):
    TIMESHEET_REMINDER = "timesheet_reminder"
    TIMESHEET_SUBMITTED = "timesheet_submitted"
    TIMESHEET_APPROVED = "timesheet_approved"
    TIMESHEET_REJECTED = "timesheet_rejected"
    ORG_INVITATION = "org_invitation"
    MEMBER_JOINED = "member_joined"
    PROJECT_ASSIGNED = "project_assigned"
    BUDGET_WARNING = "budget_warning"
    TIMER_REMINDER = "timer_reminder"
    SYSTEM = "system"


class UserStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
