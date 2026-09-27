import axios from 'axios';

const API_BASE = '/api';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT from localStorage to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aod_token');
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  r => r,
  async err => {
    const original = err.config;
    if (err?.response?.status === 401 && !original._retried) {
      original._retried = true;
      const refresh = localStorage.getItem('aod_refresh');
      if (refresh && !window.location.pathname.includes('/login')) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refresh });
          const newToken = res.data.access_token;
          localStorage.setItem('aod_token', newToken);
          // Refresh token rotation — save the new one if server issued it
          if (res.data.refresh_token) {
            localStorage.setItem('aod_refresh', res.data.refresh_token);
          }
          original.headers.Authorization = `Bearer ${newToken}`;
          return api(original);
        } catch {
          localStorage.removeItem('aod_token');
          localStorage.removeItem('aod_refresh');
          localStorage.removeItem('aod_user');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(err);
  }
);

export interface Opportunity {
  id: number;
  title: string;
  description: string;
  opportunity_score: number;
  confidence_score: number;
  demand_score: number;
  research_gap_score: number;
  trend_score: number;
  innovation_score: number;
  competition_score: number;
  feasibility_score: number;
  market_readiness_score: number;
  explanation?: string;
  created_at?: string;
}

export interface ProblemCluster {
  id: number;
  title: string;
  description: string;
  keywords: string[];
  source_count: number;
  demand_score: number;
}

export interface ResearchGap {
  id: number;
  title: string;
  description: string;
  gap_score: number;
}

export interface Trend {
  id: number;
  name: string;
  category: string;
  trend_score: number;
  growth_rate?: number;
  recent_avg?: number;
  prior_avg?: number;
  label?: 'rising' | 'declining' | 'stable' | 'new' | 'no_data';
  detected_at?: string;
}

export const getHealth = () => api.get('/health').then(r => r.data);
export const getOpportunities = () => api.get<Opportunity[]>('/opportunities').then(r => r.data);
export const getProblems = () => api.get<ProblemCluster[]>('/problems').then(r => r.data);
export const getResearchGaps = () => api.get<ResearchGap[]>('/research-gaps').then(r => r.data);
export const getTrends = () => api.get<Trend[]>('/trends').then(r => r.data);
export const getTrendHistory = (name: string, days: number = 30) =>
  api.get(`/trends/${encodeURIComponent(name)}/history?days=${days}`).then(r => r.data);

export const runPipeline = (query: string) =>
  api.post('/pipeline/run', { query }).then(r => r.data);

export const askAI = (question: string) =>
  api.post('/chat', { question }).then(r => r.data);

export const semanticSearch = (query: string) =>
  api.post('/search', { query }).then(r => r.data);


export const downloadPDFReport = async () => {
  const token = localStorage.getItem('aod_token');
  const response = await fetch('/api/reports/pdf', {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error('Failed to generate PDF');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `opportunity_report_${new Date().toISOString().slice(0, 10)}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
};

export const getSearchHistory = () =>
  api.get('/search-history').then(r => r.data);

export const getChatHistory = () =>
  api.get('/chat-history').then(r => r.data);


export const getOpportunityDetail = (id: number) =>
  api.get(`/opportunities/${id}`).then(r => r.data);

export const getChatSession = (id: number) =>
  api.get(`/chat-sessions/${id}`).then(r => r.data);

export const getSchedulerStatus = () =>
  api.get('/scheduler/status').then(r => r.data);


// Admin
export const adminGetStats = () => api.get('/admin/stats').then(r => r.data);
export const adminGetUsers = () => api.get('/admin/users').then(r => r.data);
export const adminUpdateRole = (id: number, role: string) =>
  api.patch(`/admin/users/${id}/role?role=${role}`).then(r => r.data);
export const adminDeleteUser = (id: number) => api.delete(`/admin/users/${id}`).then(r => r.data);
export const adminGetLogs = () => api.get('/admin/agent-logs').then(r => r.data);
export const adminGetScheduler = () => api.get('/admin/scheduler').then(r => r.data);
export const adminTriggerScheduler = () => api.post('/admin/scheduler/trigger').then(r => r.data);

// Forgot password
export const forgotPassword = (email: string) =>
  api.post('/auth/forgot-password', { email }).then(r => r.data);
export const resetPassword = (token: string, new_password: string) =>
  api.post('/auth/reset-password', { token, new_password }).then(r => r.data);

// Profile
export const updateProfile = (data: { name?: string; email?: string }) =>
  api.patch('/auth/me', data).then(r => r.data);
export const changePassword = (old_password: string, new_password: string) =>
  api.post('/auth/change-password', { old_password, new_password }).then(r => r.data);

// Notifications
export const getNotifications = () => api.get('/notifications').then(r => r.data);
export const getUnreadCount = () => api.get('/notifications/unread-count').then(r => r.data);
export const markNotificationRead = (id: number) => api.post(`/notifications/${id}/read`).then(r => r.data);
export const markAllNotificationsRead = () => api.post('/notifications/read-all').then(r => r.data);

// Knowledge Graph
export const getKGStats = () => api.get('/kg/stats').then(r => r.data);
export const getKGEntityTypes = () =>
  api.get('/kg/entity-types').then(r => r.data);
export const getKGNodes = (params: { entity_type?: string; limit?: number } = {}) =>
  api.get('/kg/nodes', { params }).then(r => r.data);
export const getKGEdgesList = (params: { relation?: string; limit?: number } = {}) =>
  api.get('/kg/edges', { params }).then(r => r.data);
export const getKGSemanticChain = (name: string, depth: number = 2) =>
  api.get(`/kg/semantic-chain/${encodeURIComponent(name)}?depth=${depth}`).then(r => r.data);

// Admin — Config & Sync
export const adminGetSettings = () => api.get('/admin/settings').then(r => r.data);
export const adminUpdateSetting = (key: string, value: string) =>
  api.patch('/admin/settings', { key, value }).then(r => r.data);
export const adminGetSyncStatus = () => api.get('/admin/sync/status').then(r => r.data);
export const adminTriggerSync = (topic: string, mode: 'quick' | 'deep') =>
  api.post('/admin/sync/trigger', { topic, mode }).then(r => r.data);

// JSON exports
const downloadFile = async (url: string, filename: string) => {
  const token = localStorage.getItem('aod_token');
  const response = await fetch(`/api${url}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error(`Export failed: ${response.status}`);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = objectUrl;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(objectUrl);
};

export const downloadOpportunitiesJSON = () =>
  downloadFile('/export/opportunities.json', `opportunities_${new Date().toISOString().slice(0,10)}.json`);
export const downloadGapsJSON = () =>
  downloadFile('/export/research-gaps.json', `research_gaps_${new Date().toISOString().slice(0,10)}.json`);
export const downloadFullJSON = () =>
  downloadFile('/export/full.json', `full_export_${new Date().toISOString().slice(0,10)}.json`);

export const adminGetLLMStatus = () => api.get('/admin/llm/status').then(r => r.data);
