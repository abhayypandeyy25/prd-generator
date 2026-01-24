import axios from 'axios'

// Use environment variable for API URL, fallback to /api for production (same domain)
// In development, use localhost:5001
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5001/api' : '/api')

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 300000 // 5 minutes for long-running AI operations
})

// Add request interceptor to include Firebase auth token
api.interceptors.request.use(async (config) => {
  // Dynamically import to avoid circular dependency
  const { useAuthStore } = await import('../stores/authStore')
  const authStore = useAuthStore()

  const token = await authStore.getIdToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
}, (error) => {
  return Promise.reject(error)
})

// Add response interceptor to handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, sign out user
      const { useAuthStore } = await import('../stores/authStore')
      const authStore = useAuthStore()
      await authStore.signOut()
    }
    return Promise.reject(error)
  }
)

// Projects API
export const projectsApi = {
  list: () => api.get('/projects'),
  create: (name) => api.post('/projects', { name }),
  get: (id) => api.get(`/projects/${id}`),
  delete: (id) => api.delete(`/projects/${id}`)
}

// Context API - Updated for Vercel serverless structure
export const contextApi = {
  upload: (projectId, files) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    return api.post(`/context/upload/${projectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  list: (projectId) => api.get(`/context/${projectId}`),
  delete: (fileId) => api.delete(`/context/file/${fileId}`),
  getText: (projectId) => api.get(`/context/text/${projectId}`),
  // Smart Context Analysis endpoints
  analyze: (projectId) => api.get(`/context/analyze/${projectId}`),
  deepAnalyze: (projectId) => api.post(`/context/analyze/${projectId}`),
  summarize: (fileId) => api.get(`/context/summarize/${fileId}`)
}

// Questions API - Updated for Vercel serverless structure
export const questionsApi = {
  getAll: () => api.get('/questions'),
  prefill: (projectId) => api.post(`/questions/prefill/${projectId}`),
  getResponses: (projectId) => api.get(`/questions/responses/${projectId}`),
  saveResponses: (projectId, responses) => api.put(`/questions/responses/${projectId}`, { responses }),
  updateResponse: (projectId, questionId, data) => api.put(`/questions/response/${projectId}/${questionId}`, data),
  confirmResponse: (projectId, questionId, confirmed) => api.post(`/questions/confirm/${projectId}/${questionId}`, { confirmed }),
  getStats: (projectId) => api.get(`/questions/stats/${projectId}`),
  // Adaptive questioning endpoints
  getFollowUps: (projectId, questionId, data) => api.post(`/questions/follow-ups/${projectId}/${questionId}`, data),
  saveFollowUp: (projectId, data) => api.post(`/questions/save-follow-up/${projectId}`, data),
  smartSuggest: (projectId, questionId, question) => api.post(`/questions/smart-suggest/${projectId}/${questionId}`, { question })
}

// Features API
export const featuresApi = {
  list: (projectId) => api.get(`/features/${projectId}`),
  extract: (projectId) => api.post(`/features/extract/${projectId}`),
  create: (projectId, data) => api.post(`/features/${projectId}`, data),
  update: (featureId, data) => api.put(`/features/item/${featureId}`, data),
  toggleSelect: (featureId, isSelected) => api.put(`/features/select/${featureId}`, { is_selected: isSelected }),
  delete: (featureId) => api.delete(`/features/item/${featureId}`)
}

// Templates API
export const templatesApi = {
  list: () => api.get('/templates'),
  get: (templateId) => api.get(`/templates/${templateId}`),
  create: (data) => api.post('/templates', data),
  update: (templateId, data) => api.put(`/templates/${templateId}`, data),
  clone: (templateId, name) => api.post(`/templates/${templateId}/clone`, { name }),
  delete: (templateId) => api.delete(`/templates/${templateId}`),
  getSections: (templateId) => api.get(`/templates/${templateId}/sections`)
}

// PRD API - Updated for Vercel serverless structure
export const prdApi = {
  generate: (projectId) => api.post(`/prd/generate/${projectId}`),
  get: (projectId) => api.get(`/prd/${projectId}`),
  preview: (projectId) => api.get(`/prd/preview/${projectId}`),
  exportMarkdown: (projectId) => api.get(`/prd/export/md/${projectId}`, { responseType: 'blob' }),
  exportDocx: (projectId) => api.get(`/prd/export/docx/${projectId}`, { responseType: 'blob' }),
  // PRD Editing endpoints
  edit: (projectId, content) => api.put(`/prd/edit/${projectId}`, { content_md: content }),
  getHistory: (projectId) => api.get(`/prd/history/${projectId}`),
  restore: (projectId, snapshotId) => api.post(`/prd/restore/${projectId}/${snapshotId}`),
  saveVersion: (projectId, versionName, changeSummary) => api.post(`/prd/save-version/${projectId}`, { version_name: versionName, change_summary: changeSummary }),
  regenerateSection: (projectId, sectionName) => api.post(`/prd/regenerate-section/${projectId}`, { section_name: sectionName }),
  // Version comparison endpoints
  getSnapshot: (snapshotId) => api.get(`/prd/snapshot/${snapshotId}`),
  compare: (projectId, version1Id, version2Id) => api.post(`/prd/compare/${projectId}`, { version1_id: version1Id, version2_id: version2Id }),
  changelog: (projectId, fromVersionId, toVersionId, versionName) => api.post(`/prd/changelog/${projectId}`, { from_version_id: fromVersionId, to_version_id: toVersionId, version_name: versionName })
}

// Sharing API
export const shareApi = {
  create: (projectId, options) => api.post(`/share/create/${projectId}`, options),
  get: (shareToken, password) => api.get(`/share/${shareToken}${password ? `?password=${password}` : ''}`),
  list: (projectId) => api.get(`/share/list/${projectId}`),
  revoke: (shareId) => api.delete(`/share/revoke/${shareId}`)
}

// Comments API
export const commentsApi = {
  list: (prdId) => api.get(`/comments/${prdId}`),
  add: (prdId, comment) => api.post(`/comments/${prdId}/add`, comment),
  reply: (commentId, reply) => api.post(`/comments/reply/${commentId}`, reply),
  resolve: (commentId) => api.post(`/comments/resolve/${commentId}`),
  delete: (commentId) => api.delete(`/comments/delete/${commentId}`)
}

// Stakeholder API
export const stakeholderApi = {
  getProfiles: () => api.get('/stakeholder/profiles'),
  getView: (projectId, role) => api.get(`/stakeholder/view/${projectId}/${role}`),
  generateSummary: (projectId, role) => api.post(`/stakeholder/summary/${projectId}/${role}`)
}

// Feedback API (AI Improvement Loop)
export const feedbackApi = {
  ratePRD: (projectId, rating, feedbackText, sectionName) => api.post(`/feedback/rate/${projectId}`, { rating, feedback_text: feedbackText, section_name: sectionName }),
  rateQuestion: (projectId, questionId, data) => api.post(`/feedback/question/${projectId}/${questionId}`, data),
  getStats: (projectId) => api.get(`/feedback/stats/${projectId}`),
  getSuggestions: (projectId) => api.get(`/feedback/suggestions/${projectId}`),
  improveWithFeedback: (projectId) => api.post(`/feedback/improve/${projectId}`)
}

// Analytics API
export const analyticsApi = {
  getOverview: () => api.get('/analytics/overview'),
  getProjectAnalytics: (projectId) => api.get(`/analytics/project/${projectId}`),
  getTimeline: (projectId) => api.get(`/analytics/timeline/${projectId}`)
}

export default api
