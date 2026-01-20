import axios from 'axios'

// Use environment variable for API URL, fallback to relative path for dev
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Projects API
export const projectsApi = {
  list: () => api.get('/projects'),
  create: (name) => api.post('/projects', { name }),
  get: (id) => api.get(`/projects/${id}`),
  delete: (id) => api.delete(`/projects/${id}`)
}

// Context API
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
  getText: (projectId) => api.get(`/context/${projectId}/text`)
}

// Questions API
export const questionsApi = {
  getAll: () => api.get('/questions'),
  prefill: (projectId) => api.post(`/questions/prefill/${projectId}`),
  getResponses: (projectId) => api.get(`/questions/${projectId}/responses`),
  saveResponses: (projectId, responses) => api.put(`/questions/${projectId}/responses`, { responses }),
  updateResponse: (projectId, questionId, data) => api.put(`/questions/${projectId}/response/${questionId}`, data),
  confirmResponse: (projectId, questionId, confirmed) => api.post(`/questions/${projectId}/confirm/${questionId}`, { confirmed }),
  getStats: (projectId) => api.get(`/questions/${projectId}/stats`)
}

// PRD API
export const prdApi = {
  generate: (projectId) => api.post(`/prd/generate/${projectId}`),
  get: (projectId) => api.get(`/prd/${projectId}`),
  preview: (projectId) => api.get(`/prd/${projectId}/preview`),
  exportMarkdown: (projectId) => api.get(`/prd/${projectId}/export/md`, { responseType: 'blob' }),
  exportDocx: (projectId) => api.get(`/prd/${projectId}/export/docx`, { responseType: 'blob' })
}

export default api
