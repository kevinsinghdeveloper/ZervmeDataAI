const apiService = {
  // Auth
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  respondToChallenge: jest.fn(),
  requestPasswordReset: jest.fn(),
  resetPassword: jest.fn(),
  verifyEmail: jest.fn(),
  acceptInvitation: jest.fn(),
  getOAuthUrl: jest.fn(),
  oauthCallback: jest.fn(),

  // Users
  getCurrentUser: jest.fn(),
  listUsers: jest.fn(),
  updateUserRole: jest.fn(),
  updateUser: jest.fn(),
  deleteUser: jest.fn(),
  updatePreferences: jest.fn(),

  // Organizations
  getCurrentOrg: jest.fn(),
  updateOrg: jest.fn(),
  createOrg: jest.fn(),
  listOrgInvitations: jest.fn(),
  createOrgInvitation: jest.fn(),
  deleteOrgInvitation: jest.fn(),
  listOrgMembers: jest.fn(),
  updateMemberRole: jest.fn(),
  removeMember: jest.fn(),
  listMemberRoles: jest.fn(),
  addMemberRole: jest.fn(),
  removeMemberRole: jest.fn(),
  listMyOrgs: jest.fn(),

  // Projects
  listProjects: jest.fn(),
  createProject: jest.fn(),
  getProject: jest.fn(),
  updateProject: jest.fn(),
  deleteProject: jest.fn(),

  // AI Chat
  listChatSessions: jest.fn(),
  createChatSession: jest.fn(),
  getChatSession: jest.fn(),
  deleteChatSession: jest.fn(),
  listChatMessages: jest.fn(),
  sendChatMessage: jest.fn(),
  listAIModels: jest.fn(),
  updateAIModel: jest.fn(),
  deleteAIModelConfig: jest.fn(),

  // Notifications
  listNotifications: jest.fn(),
  markNotificationRead: jest.fn(),
  markAllNotificationsRead: jest.fn(),
  getUnreadNotificationCount: jest.fn(),

  // Super Admin
  superAdminListOrgs: jest.fn(),
  superAdminListUsers: jest.fn(),
  superAdminGetStats: jest.fn(),
  superAdminUpdateOrg: jest.fn(),
  superAdminToggleUser: jest.fn(),
  superAdminResetPassword: jest.fn(),
  superAdminGrantSuperAdmin: jest.fn(),
  superAdminRevokeSuperAdmin: jest.fn(),

  // Config
  getThemeConfig: jest.fn(),
  saveThemeConfig: jest.fn(),
  getSettings: jest.fn(),
  saveSettings: jest.fn(),

  // Audit
  getAuditLogs: jest.fn(),
};

export default apiService;
