import axios, { AxiosInstance } from 'axios';
import { API_CONFIG } from '../configs/api.config';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_CONFIG.API_BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: { 'Content-Type': 'application/json' },
    });

    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      const orgId = localStorage.getItem('currentOrgId');
      if (orgId) {
        config.headers['X-Org-Id'] = orgId;
      }
      return config;
    });

    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 && localStorage.getItem('authToken')) {
          localStorage.removeItem('authToken');
          localStorage.removeItem('user');
          localStorage.removeItem('currentOrgId');
          window.location.href = '/login';
        }
        const message =
          error.response?.data?.error ||
          error.response?.data?.message ||
          error.message ||
          'An unexpected error occurred';
        return Promise.reject(new Error(message));
      }
    );
  }

  // ==================== Auth ====================
  async login(email: string, password: string) {
    const response = await this.api.post('/api/auth/login', { email, password });
    return response.data;
  }

  async register(data: { email: string; password: string; firstName: string; lastName: string; invitationToken?: string }) {
    const response = await this.api.post('/api/auth/register', data);
    return response.data;
  }

  async logout() {
    const response = await this.api.post('/api/auth/logout');
    return response.data;
  }

  async respondToChallenge(email: string, newPassword: string, session: string) {
    const response = await this.api.post('/api/auth/challenge', { email, newPassword, session });
    return response.data;
  }

  async requestPasswordReset(email: string) {
    const response = await this.api.post('/api/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(email: string, code: string, newPassword: string) {
    const response = await this.api.post('/api/auth/reset-password', { email, code, newPassword });
    return response.data;
  }

  async verifyEmail(email: string, code: string) {
    const response = await this.api.post('/api/auth/verify-email', { email, code });
    return response.data;
  }

  async acceptInvitation(token: string) {
    const response = await this.api.post('/api/auth/accept-invitation', { token });
    return response.data;
  }

  // OAuth
  async getOAuthUrl(provider: string, redirectUri: string) {
    const response = await this.api.get(`/api/auth/oauth/${provider}/authorize`, { params: { redirect_uri: redirectUri } });
    return response.data;
  }

  async oauthCallback(provider: string, code: string, redirectUri: string) {
    const response = await this.api.post(`/api/auth/oauth/${provider}/callback`, { code, redirect_uri: redirectUri });
    return response.data;
  }

  // ==================== Users ====================
  async getCurrentUser() {
    const response = await this.api.get('/api/users/me');
    return response.data;
  }

  async listUsers(page: number = 1, perPage: number = 20) {
    const response = await this.api.get('/api/users', { params: { page, per_page: perPage } });
    return response.data;
  }

  async updateUserRole(userId: string, role: string) {
    const response = await this.api.put(`/api/users/${userId}/role`, { role });
    return response.data;
  }

  async updateUser(userId: string, data: any) {
    const response = await this.api.put(`/api/users/${userId}`, data);
    return response.data;
  }

  async deleteUser(userId: string) {
    const response = await this.api.delete(`/api/users/${userId}`);
    return response.data;
  }

  async updatePreferences(data: any) {
    const response = await this.api.put('/api/users/me/preferences', data);
    return response.data;
  }

  // ==================== Organizations ====================
  async getCurrentOrg() {
    const response = await this.api.get('/api/organizations/current');
    return response.data;
  }

  async updateOrg(data: any) {
    const response = await this.api.put('/api/organizations/current', data);
    return response.data;
  }

  async createOrg(data: { name: string }) {
    const response = await this.api.post('/api/organizations', data);
    return response.data;
  }

  async listOrgInvitations() {
    const response = await this.api.get('/api/organizations/invitations');
    return response.data;
  }

  async createOrgInvitation(email: string, role: string = 'member') {
    const response = await this.api.post('/api/organizations/invitations', { email, role });
    return response.data;
  }

  async deleteOrgInvitation(invitationId: string) {
    const response = await this.api.delete(`/api/organizations/invitations/${invitationId}`);
    return response.data;
  }

  async listOrgMembers() {
    const response = await this.api.get('/api/organizations/members');
    return response.data;
  }

  async updateMemberRole(memberId: string, role: string) {
    const response = await this.api.put(`/api/organizations/members/${memberId}/role`, { role });
    return response.data;
  }

  async removeMember(memberId: string) {
    const response = await this.api.delete(`/api/organizations/members/${memberId}`);
    return response.data;
  }

  async listMemberRoles(memberId: string) {
    const response = await this.api.get(`/api/organizations/members/${memberId}/roles`);
    return response.data;
  }

  async addMemberRole(memberId: string, role: string) {
    const response = await this.api.post(`/api/organizations/members/${memberId}/roles`, { role });
    return response.data;
  }

  async removeMemberRole(memberId: string, role: string) {
    const response = await this.api.delete(`/api/organizations/members/${memberId}/roles/${role}`);
    return response.data;
  }

  async listMyOrgs() {
    const response = await this.api.get('/api/users/me/orgs');
    return response.data;
  }

  // ==================== Projects ====================
  async listProjects(params?: { status?: string }) {
    const response = await this.api.get('/api/projects', { params });
    return response.data;
  }

  async createProject(data: any) {
    const response = await this.api.post('/api/projects', data);
    return response.data;
  }

  async getProject(id: string) {
    const response = await this.api.get(`/api/projects/${id}`);
    return response.data;
  }

  async updateProject(id: string, data: any) {
    const response = await this.api.put(`/api/projects/${id}`, data);
    return response.data;
  }

  async deleteProject(id: string) {
    const response = await this.api.delete(`/api/projects/${id}`);
    return response.data;
  }

  // ==================== AI Chat ====================
  async listChatSessions() {
    const response = await this.api.get('/api/ai/sessions');
    return response.data;
  }

  async createChatSession(title?: string) {
    const response = await this.api.post('/api/ai/sessions', { title });
    return response.data;
  }

  async getChatSession(sessionId: string) {
    const response = await this.api.get(`/api/ai/sessions/${sessionId}`);
    return response.data;
  }

  async deleteChatSession(sessionId: string) {
    const response = await this.api.delete(`/api/ai/sessions/${sessionId}`);
    return response.data;
  }

  async listChatMessages(sessionId: string) {
    const response = await this.api.get(`/api/ai/sessions/${sessionId}/messages`);
    return response.data;
  }

  async sendChatMessage(sessionId: string, content: string, modelId?: string) {
    const response = await this.api.post(`/api/ai/sessions/${sessionId}/message`, { content, modelId });
    return response.data;
  }

  async listAIModels() {
    const response = await this.api.get('/api/ai/models');
    return response.data;
  }

  async updateAIModel(data: any) {
    const response = await this.api.post('/api/ai/models', data);
    return response.data;
  }

  async deleteAIModelConfig(modelId: string) {
    const response = await this.api.delete(`/api/ai/models/${modelId}`);
    return response.data;
  }

  // ==================== Notifications ====================
  async listNotifications() {
    const response = await this.api.get('/api/notifications');
    return response.data;
  }

  async markNotificationRead(notificationId: string) {
    const response = await this.api.put(`/api/notifications/${notificationId}/read`);
    return response.data;
  }

  async markAllNotificationsRead() {
    const response = await this.api.post('/api/notifications/read-all');
    return response.data;
  }

  async getUnreadNotificationCount() {
    const response = await this.api.get('/api/notifications/unread-count');
    return response.data;
  }

  // ==================== Super Admin ====================
  async superAdminListOrgs(page?: number, perPage?: number) {
    const response = await this.api.get('/api/super-admin/organizations', { params: { page, per_page: perPage } });
    return response.data;
  }

  async superAdminListUsers(page?: number, perPage?: number) {
    const response = await this.api.get('/api/super-admin/users', { params: { page, per_page: perPage } });
    return response.data;
  }

  async superAdminGetStats() {
    const response = await this.api.get('/api/super-admin/stats');
    return response.data;
  }

  async superAdminUpdateOrg(orgId: string, data: any) {
    const response = await this.api.put(`/api/super-admin/organizations/${orgId}`, data);
    return response.data;
  }

  async superAdminToggleUser(userId: string) {
    const response = await this.api.put(`/api/super-admin/users/${userId}/toggle`);
    return response.data;
  }

  async superAdminResetPassword(userId: string, newPassword: string) {
    const response = await this.api.post(`/api/super-admin/users/${userId}/reset-password`, { newPassword });
    return response.data;
  }

  async superAdminGrantSuperAdmin(userId: string) {
    const response = await this.api.post('/api/super-admin/grant-super-admin', { target_user_id: userId });
    return response.data;
  }

  async superAdminRevokeSuperAdmin(userId: string) {
    const response = await this.api.delete('/api/super-admin/revoke-super-admin', { data: { target_user_id: userId } });
    return response.data;
  }

  // ==================== Config ====================
  async getThemeConfig() {
    const response = await this.api.get('/api/config/theme');
    return response.data;
  }

  async saveThemeConfig(config: any) {
    const response = await this.api.post('/api/config/theme', config);
    return response.data;
  }

  async getSettings() {
    const response = await this.api.get('/api/config/settings');
    return response.data;
  }

  async saveSettings(data: any) {
    const response = await this.api.post('/api/config/settings', data);
    return response.data;
  }

  // ==================== Audit ====================
  async getAuditLogs(params?: { page?: number; per_page?: number; action?: string; user_id?: string }) {
    const response = await this.api.get('/api/audit/logs', { params });
    return response.data;
  }

  // ==================== Reports ====================
  async listReports(params?: { project_id?: string }) {
    const response = await this.api.get('/api/reports', { params });
    return response.data;
  }

  async createReport(data: any) {
    const response = await this.api.post('/api/reports', data);
    return response.data;
  }

  async getReport(id: string) {
    const response = await this.api.get(`/api/reports/${id}`);
    return response.data;
  }

  async updateReport(id: string, data: any) {
    const response = await this.api.put(`/api/reports/${id}`, data);
    return response.data;
  }

  async deleteReport(id: string) {
    const response = await this.api.delete(`/api/reports/${id}`);
    return response.data;
  }

  // ==================== Report Processor ====================
  async startReportJob(data: { report_id: string; report_name?: string; task_params?: any; llm_config?: any }) {
    const response = await this.api.post('/api/report-processor/start', data);
    return response.data;
  }

  async getReportJobStatus(jobId: string) {
    const response = await this.api.get(`/api/report-processor/status/${jobId}`);
    return response.data;
  }

  async stopReportJob(jobId: string) {
    const response = await this.api.post(`/api/report-processor/stop/${jobId}`);
    return response.data;
  }

  // ==================== Datasets ====================
  async listDatasets() {
    const response = await this.api.get('/api/datasets');
    return response.data;
  }

  async createDataset(data: any) {
    const response = await this.api.post('/api/datasets', data);
    return response.data;
  }

  async getDataset(id: string) {
    const response = await this.api.get(`/api/datasets/${id}`);
    return response.data;
  }

  async updateDataset(id: string, data: any) {
    const response = await this.api.put(`/api/datasets/${id}`, data);
    return response.data;
  }

  async deleteDataset(id: string) {
    const response = await this.api.delete(`/api/datasets/${id}`);
    return response.data;
  }

  // ==================== Model Configs ====================
  async listModelConfigs() {
    const response = await this.api.get('/api/model-configs');
    return response.data;
  }

  async createModelConfig(data: any) {
    const response = await this.api.post('/api/model-configs', data);
    return response.data;
  }

  async getModelConfig(id: string) {
    const response = await this.api.get(`/api/model-configs/${id}`);
    return response.data;
  }

  async updateModelConfig(id: string, data: any) {
    const response = await this.api.put(`/api/model-configs/${id}`, data);
    return response.data;
  }

  async deleteModelConfig(id: string) {
    const response = await this.api.delete(`/api/model-configs/${id}`);
    return response.data;
  }

  // ==================== Dashboard ====================
  async getDashboardForReport(reportId: string) {
    const response = await this.api.get(`/api/dashboard/report/${reportId}`);
    return response.data;
  }

  async getDashboardOverview() {
    const response = await this.api.get('/api/dashboard/overview');
    return response.data;
  }
}

const apiService = new ApiService();
export default apiService;
