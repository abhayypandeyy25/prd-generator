import axios from 'axios'

// Use environment variable for API URL, fallback to /api for production (same domain)
// In development, use localhost:5001
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5001/api' : '/api')

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
  getText: (projectId) => api.get(`/context/text/${projectId}`)
}

// Questions API - Updated for Vercel serverless structure
export const questionsApi = {
  getAll: () => api.get('/questions'),
  prefill: (projectId) => api.post(`/questions/prefill/${projectId}`),
  getResponses: (projectId) => api.get(`/questions/responses/${projectId}`),
  saveResponses: (projectId, responses) => api.put(`/questions/responses/${projectId}`, { responses }),
  updateResponse: (projectId, questionId, data) => api.put(`/questions/response/${projectId}/${questionId}`, data),
  confirmResponse: (projectId, questionId, confirmed) => api.post(`/questions/confirm/${projectId}/${questionId}`, { confirmed }),
  getStats: (projectId) => api.get(`/questions/stats/${projectId}`)
}

// PRD API - Updated for Vercel serverless structure
export const prdApi = {
  generate: (projectId) => api.post(`/prd/generate/${projectId}`),
  get: (projectId) => api.get(`/prd/${projectId}`),
  preview: (projectId) => api.get(`/prd/preview/${projectId}`),
  exportMarkdown: (projectId) => api.get(`/prd/export/md/${projectId}`, { responseType: 'blob' }),
  exportDocx: (projectId) => api.get(`/prd/export/docx/${projectId}`, { responseType: 'blob' })
}

export default api
