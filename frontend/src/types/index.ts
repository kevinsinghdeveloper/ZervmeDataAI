// ==================== Enums & Constants ====================
export type OrgRole = 'owner' | 'admin' | 'manager' | 'member';
export type GlobalRole = 'global_admin' | 'user';
export type UserStatus = 'invited' | 'active' | 'deactivated';
export type ProjectStatus = 'active' | 'archived' | 'completed';
export type NotificationType = 'org_invitation' | 'member_joined' | 'project_assigned' | 'system';

// Legacy compat
export type Role = 'admin' | 'editor' | 'viewer' | 'lendee' | 'owner' | 'manager' | 'member';

export const ORG_ROLE_HIERARCHY: OrgRole[] = ['member', 'manager', 'admin', 'owner'];

export const ORG_ROLE_PERMISSIONS: Record<OrgRole, string[]> = {
  member: ['view_projects'],
  manager: ['view_projects', 'manage_projects'],
  admin: ['view_projects', 'manage_projects', 'manage_users', 'view_reports'],
  owner: ['view_projects', 'manage_projects', 'manage_users', 'view_reports', 'manage_org'],
};

// ==================== Role Types ====================
export interface UserRole {
  userId: string;
  orgId: string;
  role: OrgRole | 'super_admin';
  grantedBy?: string;
  grantedAt: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface OrgMembership {
  orgId: string;
  roles: OrgRole[];
  grantedAt: string;
}

// ==================== User Types ====================
export interface User {
  id: string;
  email: string;
  username?: string;
  firstName: string;
  lastName: string;
  orgId?: string;
  orgRole: OrgRole;
  orgRoles?: OrgRole[];
  isSuperAdmin: boolean;
  role: Role;
  isActive: boolean;
  isVerified: boolean;
  status: UserStatus;
  timezone: string;
  avatarUrl?: string;
  phone?: string;
  notificationPreferences?: NotificationPreferences;
  oauthProviders?: Record<string, { provider_user_id: string; linked_at: string }>;
  mustResetPassword?: boolean;
  invitedAt?: string;
  orgMemberships?: OrgMembership[];
  createdAt: string;
  updatedAt: string;
}

export interface NotificationPreferences {
  inAppNotifications: boolean;
  desktopNotifications: boolean;
  emailNotifications: boolean;
}

export interface UserPreferences {
  timezone: string;
  notificationPreferences: NotificationPreferences;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  refreshToken?: string;
  accessToken?: string;
  user: User;
  challengeName?: string;
  session?: string;
  email?: string;
}

// ==================== Organization Types ====================
export interface Organization {
  id: string;
  name: string;
  slug: string;
  ownerId: string;
  logoUrl?: string;
  settings?: OrgSettings;
  memberCount: number;
  isActive: boolean;
  userRoles?: OrgRole[];
  createdAt: string;
  updatedAt: string;
}

export interface OrgSettings {
  timezone: string;
}

export interface OrgInvite {
  id: string;
  orgId: string;
  email: string;
  role: OrgRole;
  status: 'pending' | 'accepted' | 'expired' | 'revoked';
  invitedBy: string;
  expiresAt: string;
  acceptedAt?: string;
  createdAt: string;
}

// ==================== Project Types ====================
export interface Project {
  orgId: string;
  id: string;
  name: string;
  description?: string;
  projectType?: string;
  status: ProjectStatus;
  createdAt: string;
  updatedAt: string;
}

// ==================== Notification Types ====================
export interface AppNotification {
  userId: string;
  id: string;
  orgId?: string;
  type: NotificationType;
  title: string;
  message: string;
  isRead: boolean;
  actionUrl?: string;
  createdAt: string;
}

// ==================== AI Chat Types ====================
export interface AIChatSession {
  userId: string;
  id: string;
  orgId: string;
  title: string;
  messageCount: number;
  lastMessageAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AIChatMessage {
  sessionId: string;
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  chartConfig?: Record<string, any>;
  createdAt: string;
}

// ==================== AI Model Config Types ====================
export type AIModelProvider = 'openai' | 'anthropic' | 'custom';

export interface AIModelConfig {
  id: string;
  name: string;
  modelId: string;
  provider: AIModelProvider;
  maxContext: number;
  isActive: boolean;
  isDefault: boolean;
  config: {
    temperature: number;
    maxTokens: number;
    hasApiKey: boolean;
  };
  createdAt?: string;
  updatedAt?: string;
}

export interface AIModelUpdateRequest {
  modelId: string;
  name?: string;
  provider?: string;
  model_name?: string;
  isActive?: boolean;
  isDefault?: boolean;
  apiKey?: string;
  config?: string | { temperature?: number; maxTokens?: number };
}

// ==================== Theme Config Types ====================
export interface ThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    tertiary?: string;
    background?: string;
    paper?: string;
  };
  logo?: string;
  appName: string;
  favicon?: string;
  mode?: 'dark' | 'light';
}

// ==================== API Response Types ====================
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ==================== Audit Types ====================
export interface AuditLogEntry {
  id: string;
  userId: string;
  orgId?: string;
  action: string;
  resource: string;
  resourceId?: string;
  details?: Record<string, any>;
  timestamp: string;
  ipAddress?: string;
}

// ==================== RBAC Types ====================
export interface RBACPermission {
  resource: string;
  actions: string[];
}

export const ROLE_PERMISSIONS: Record<string, RBACPermission[]> = {
  admin: [{ resource: '*', actions: ['*'] }],
  owner: [{ resource: '*', actions: ['*'] }],
  manager: [
    { resource: 'projects', actions: ['read'] },
  ],
  member: [
    { resource: 'projects', actions: ['read'] },
  ],
  editor: [{ resource: 'content', actions: ['create', 'read', 'update'] }],
  viewer: [{ resource: 'content', actions: ['read'] }],
  lendee: [{ resource: 'documents', actions: ['create', 'read', 'delete'] }],
};

// ==================== Report Types ====================
export type ReportStatus = 'draft' | 'active' | 'archived';

export interface ReportInfo {
  orgId: string;
  id: string;
  name: string;
  projectId?: string;
  reportTypeId?: string;
  modelId?: string;
  datasetConfig?: string;
  reportConfig?: string;
  status: ReportStatus;
  lastRunDate?: string;
  createdAt: string;
  updatedAt: string;
}

// ==================== Report Job Types ====================
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ReportJob {
  orgId: string;
  id: string;
  reportId: string;
  status: JobStatus;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
  resultData?: string;
  createdAt: string;
  updatedAt: string;
}

// ==================== Dataset Types ====================
export type DatasetStatus = 'active' | 'inactive' | 'processing';

export interface DatasetInfo {
  orgId: string;
  id: string;
  name: string;
  description?: string;
  domainData?: string;
  dataSource?: string;
  status: DatasetStatus;
  createdAt: string;
  updatedAt: string;
}

// ==================== Model Config Types (ETL) ====================
export type ModelConfigStatus = 'active' | 'inactive';

export interface ModelConfig {
  orgId: string;
  id: string;
  name: string;
  modelTypeId?: string;
  modelConfig?: string;
  status: ModelConfigStatus;
  createdAt: string;
  updatedAt: string;
}

// ==================== Report Type Config ====================
export interface ReportConfigField {
  fieldName: string;
  possibleOptions: string[];
  fieldType: 0 | 1;
  isMulti?: boolean;
}

export interface ReportTypeConfig {
  fields: ReportConfigField[];
}

export interface ReportTypeInfo {
  id: string;
  name: string;
  reportConfig?: ReportTypeConfig;
}
