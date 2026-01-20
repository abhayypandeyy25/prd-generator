import { defineStore } from 'pinia'
import { projectsApi, contextApi, questionsApi, prdApi } from '../services/api'

// Helper function to extract error message from API response
function getErrorMessage(error, defaultMessage = 'An error occurred') {
  if (error.response?.data?.error) {
    return error.response.data.error
  }
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  if (error.message) {
    return error.message
  }
  return defaultMessage
}

// Helper function to check if error is a network error
function isNetworkError(error) {
  return !error.response && error.request
}

// Helper function to check if error is a server error
function isServerError(error) {
  return error.response?.status >= 500
}

export const useProjectStore = defineStore('project', {
  state: () => ({
    // Projects
    projects: [],
    currentProject: null,

    // Context Files
    contextFiles: [],
    aggregatedContext: '',

    // Questions
    questions: { sections: [] },
    responses: {},
    stats: {
      total_questions: 0,
      answered: 0,
      confirmed: 0,
      completion_percentage: 0
    },

    // PRD
    prd: null,
    prdHtml: '',

    // UI State
    loading: false,
    loadingAction: null, // Track which action is loading
    error: null,
    toast: null,
    activeTab: 'context',
    activeSection: null
  }),

  getters: {
    getResponseByQuestionId: (state) => (questionId) => {
      return state.responses[questionId] || null
    },

    confirmedCount: (state) => {
      return Object.values(state.responses).filter(r => r.confirmed).length
    },

    totalQuestions: (state) => {
      let count = 0
      state.questions.sections?.forEach(section => {
        section.subsections?.forEach(sub => {
          count += sub.questions?.length || 0
        })
      })
      return count
    },

    completionPercentage: (state) => {
      const total = state.stats.total_questions || 0
      const confirmed = state.stats.confirmed || 0
      return total > 0 ? Math.round((confirmed / total) * 100) : 0
    },

    isLoading: (state) => (action = null) => {
      if (action) {
        return state.loading && state.loadingAction === action
      }
      return state.loading
    }
  },

  actions: {
    showToast(message, type = 'info', duration = 3000) {
      this.toast = { message, type }
      setTimeout(() => {
        this.toast = null
      }, duration)
    },

    setLoading(isLoading, action = null) {
      this.loading = isLoading
      this.loadingAction = isLoading ? action : null
    },

    clearError() {
      this.error = null
    },

    // Projects
    async fetchProjects() {
      this.setLoading(true, 'fetchProjects')
      this.error = null

      try {
        const response = await projectsApi.list()
        this.projects = Array.isArray(response.data) ? response.data : []
        return this.projects
      } catch (error) {
        console.error('Failed to fetch projects:', error)

        if (isNetworkError(error)) {
          this.error = 'Unable to connect to server. Please check your connection.'
        } else if (isServerError(error)) {
          this.error = 'Server error. Please try again later.'
        } else {
          this.error = getErrorMessage(error, 'Failed to load projects')
        }

        this.projects = []
        return []
      } finally {
        this.setLoading(false)
      }
    },

    async createProject(name) {
      if (!name || !name.trim()) {
        this.showToast('Project name is required', 'error')
        throw new Error('Project name is required')
      }

      this.setLoading(true, 'createProject')

      try {
        const response = await projectsApi.create(name.trim())

        if (!response.data || !response.data.id) {
          throw new Error('Invalid response from server')
        }

        this.projects.unshift(response.data)
        this.currentProject = response.data
        this.showToast('Project created successfully', 'success')
        return response.data
      } catch (error) {
        console.error('Failed to create project:', error)

        const message = getErrorMessage(error, 'Failed to create project')
        this.showToast(message, 'error')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async selectProject(projectId) {
      if (!projectId) {
        console.warn('No project ID provided to selectProject')
        return
      }

      const project = this.projects.find(p => p.id === projectId)
      if (!project) {
        console.warn('Project not found:', projectId)
        this.showToast('Project not found', 'error')
        return
      }

      this.currentProject = project
      this.setLoading(true, 'selectProject')

      try {
        // Load project data in parallel
        await Promise.allSettled([
          this.fetchContextFiles(),
          this.fetchResponses(),
          this.fetchStats()
        ])
      } catch (error) {
        console.error('Error loading project data:', error)
      } finally {
        this.setLoading(false)
      }
    },

    async deleteProject(projectId) {
      if (!projectId) {
        this.showToast('Invalid project ID', 'error')
        return
      }

      this.setLoading(true, 'deleteProject')

      try {
        await projectsApi.delete(projectId)
        this.projects = this.projects.filter(p => p.id !== projectId)

        if (this.currentProject?.id === projectId) {
          this.currentProject = this.projects[0] || null
          // Reset related data
          this.contextFiles = []
          this.responses = {}
          this.prd = null
          this.prdHtml = ''
        }

        this.showToast('Project deleted', 'success')
      } catch (error) {
        console.error('Failed to delete project:', error)
        const message = getErrorMessage(error, 'Failed to delete project')
        this.showToast(message, 'error')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    // Context
    async uploadFiles(files) {
      if (!this.currentProject) {
        this.showToast('Please select a project first', 'error')
        return
      }

      if (!files || files.length === 0) {
        this.showToast('No files selected', 'error')
        return
      }

      this.setLoading(true, 'uploadFiles')

      try {
        const response = await contextApi.upload(this.currentProject.id, files)
        await this.fetchContextFiles()

        const { uploaded = [], errors = [], summary = {} } = response.data

        if (errors.length > 0 && uploaded.length > 0) {
          this.showToast(`${uploaded.length} files uploaded, ${errors.length} failed`, 'warning', 5000)
        } else if (errors.length > 0 && uploaded.length === 0) {
          this.showToast('All uploads failed. Check file types and sizes.', 'error', 5000)
        } else if (uploaded.length > 0) {
          this.showToast(`${uploaded.length} file${uploaded.length > 1 ? 's' : ''} uploaded successfully`, 'success')
        }

        return response.data
      } catch (error) {
        console.error('Failed to upload files:', error)
        const message = getErrorMessage(error, 'Failed to upload files')
        this.showToast(message, 'error')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async fetchContextFiles() {
      if (!this.currentProject) return []

      try {
        const response = await contextApi.list(this.currentProject.id)
        this.contextFiles = Array.isArray(response.data) ? response.data : []
        return this.contextFiles
      } catch (error) {
        console.error('Failed to fetch context files:', error)
        this.contextFiles = []
        return []
      }
    },

    async deleteContextFile(fileId) {
      if (!fileId) {
        this.showToast('Invalid file ID', 'error')
        return
      }

      try {
        await contextApi.delete(fileId)
        this.contextFiles = this.contextFiles.filter(f => f.id !== fileId)
        this.showToast('File deleted', 'success')
      } catch (error) {
        console.error('Failed to delete context file:', error)
        const message = getErrorMessage(error, 'Failed to delete file')
        this.showToast(message, 'error')
        throw error
      }
    },

    async fetchAggregatedContext() {
      if (!this.currentProject) return ''

      try {
        const response = await contextApi.getText(this.currentProject.id)
        this.aggregatedContext = response.data?.text || ''
        return this.aggregatedContext
      } catch (error) {
        console.error('Failed to fetch context:', error)
        this.aggregatedContext = ''
        return ''
      }
    },

    // Questions
    async fetchQuestions() {
      try {
        const response = await questionsApi.getAll()
        this.questions = response.data || { sections: [] }

        if (this.questions.sections?.length > 0 && !this.activeSection) {
          this.activeSection = this.questions.sections[0].id
        }

        return this.questions
      } catch (error) {
        console.error('Failed to fetch questions:', error)
        this.questions = { sections: [] }
        return this.questions
      }
    },

    async prefillQuestions() {
      if (!this.currentProject) {
        this.showToast('Please select a project first', 'error')
        return
      }

      this.setLoading(true, 'prefillQuestions')

      try {
        const response = await questionsApi.prefill(this.currentProject.id)
        await this.fetchResponses()
        await this.fetchStats()

        const message = response.data?.message || 'Questions prefilled successfully'
        this.showToast(message, 'success')
        return response.data
      } catch (error) {
        console.error('Failed to prefill questions:', error)

        let message = getErrorMessage(error, 'Failed to prefill questions')

        // Add hint if available
        if (error.response?.data?.hint) {
          message += '. ' + error.response.data.hint
        }

        this.showToast(message, 'error', 5000)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async fetchResponses() {
      if (!this.currentProject) return {}

      try {
        const response = await questionsApi.getResponses(this.currentProject.id)
        // Convert array to object keyed by question_id
        this.responses = {}
        const data = Array.isArray(response.data) ? response.data : []
        data.forEach(r => {
          if (r.question_id) {
            this.responses[r.question_id] = r
          }
        })
        return this.responses
      } catch (error) {
        console.error('Failed to fetch responses:', error)
        this.responses = {}
        return {}
      }
    },

    async saveResponse(questionId, response, confirmed = false) {
      if (!this.currentProject) {
        this.showToast('Please select a project first', 'error')
        return
      }

      if (!questionId) {
        console.error('Question ID is required')
        return
      }

      try {
        const data = {
          response: response || '',
          confirmed: Boolean(confirmed),
          ai_suggested: this.responses[questionId]?.ai_suggested || false
        }

        await questionsApi.updateResponse(this.currentProject.id, questionId, data)

        // Update local state
        this.responses[questionId] = {
          ...this.responses[questionId],
          question_id: questionId,
          response,
          confirmed
        }

        await this.fetchStats()
      } catch (error) {
        console.error('Failed to save response:', error)
        const message = getErrorMessage(error, 'Failed to save response')
        this.showToast(message, 'error')
        throw error
      }
    },

    async confirmResponse(questionId, confirmed = true) {
      if (!this.currentProject) {
        this.showToast('Please select a project first', 'error')
        return
      }

      if (!questionId) {
        console.error('Question ID is required')
        return
      }

      try {
        await questionsApi.confirmResponse(this.currentProject.id, questionId, confirmed)

        if (this.responses[questionId]) {
          this.responses[questionId].confirmed = confirmed
        }

        await this.fetchStats()
      } catch (error) {
        console.error('Failed to confirm response:', error)
        const message = getErrorMessage(error, 'Failed to confirm response')
        this.showToast(message, 'error')
        throw error
      }
    },

    async fetchStats() {
      if (!this.currentProject) return this.stats

      try {
        const response = await questionsApi.getStats(this.currentProject.id)
        this.stats = response.data || {
          total_questions: 0,
          answered: 0,
          confirmed: 0,
          completion_percentage: 0
        }
        return this.stats
      } catch (error) {
        console.error('Failed to fetch stats:', error)
        return this.stats
      }
    },

    // PRD
    async generatePRD() {
      if (!this.currentProject) {
        this.showToast('Please select a project first', 'error')
        return
      }

      this.setLoading(true, 'generatePRD')

      try {
        const response = await prdApi.generate(this.currentProject.id)
        this.prd = response.data?.content || ''
        this.showToast('PRD generated successfully', 'success')
        return response.data
      } catch (error) {
        console.error('Failed to generate PRD:', error)

        let message = getErrorMessage(error, 'Failed to generate PRD')

        // Add hint if available
        if (error.response?.data?.hint) {
          message += '. ' + error.response.data.hint
        }

        this.showToast(message, 'error', 5000)
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    async fetchPRD() {
      if (!this.currentProject) return null

      try {
        const response = await prdApi.get(this.currentProject.id)
        this.prd = response.data?.content_md || null
        return this.prd
      } catch (error) {
        // PRD might not exist yet - this is not an error
        if (error.response?.status === 404) {
          this.prd = null
          return null
        }
        console.error('Failed to fetch PRD:', error)
        this.prd = null
        return null
      }
    },

    async fetchPRDPreview() {
      if (!this.currentProject) return null

      try {
        const response = await prdApi.preview(this.currentProject.id)
        this.prd = response.data?.markdown || ''
        this.prdHtml = response.data?.html || ''
        return response.data
      } catch (error) {
        // PRD might not exist yet
        if (error.response?.status === 404) {
          this.prd = null
          this.prdHtml = ''
          return null
        }
        console.error('Failed to fetch PRD preview:', error)
        this.prd = null
        this.prdHtml = ''
        return null
      }
    },

    async exportPRD(format) {
      if (!this.currentProject) {
        this.showToast('Please select a project first', 'error')
        return
      }

      if (!['md', 'docx'].includes(format)) {
        this.showToast('Invalid export format', 'error')
        return
      }

      this.setLoading(true, 'exportPRD')

      try {
        let response
        let filename

        // Sanitize project name for filename
        const safeName = (this.currentProject.name || 'PRD')
          .replace(/[^a-zA-Z0-9\s-_]/g, '')
          .trim() || 'PRD'

        if (format === 'md') {
          response = await prdApi.exportMarkdown(this.currentProject.id)
          filename = `PRD_${safeName}.md`
        } else {
          response = await prdApi.exportDocx(this.currentProject.id)
          filename = `PRD_${safeName}.docx`
        }

        // Download file
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)

        this.showToast(`PRD exported as ${format.toUpperCase()}`, 'success')
      } catch (error) {
        console.error('Failed to export PRD:', error)
        const message = getErrorMessage(error, 'Failed to export PRD')
        this.showToast(message, 'error')
        throw error
      } finally {
        this.setLoading(false)
      }
    },

    setActiveTab(tab) {
      if (['context', 'questions', 'prd'].includes(tab)) {
        this.activeTab = tab
      }
    },

    setActiveSection(sectionId) {
      this.activeSection = sectionId
    },

    // Reset store state
    resetState() {
      this.projects = []
      this.currentProject = null
      this.contextFiles = []
      this.aggregatedContext = ''
      this.questions = { sections: [] }
      this.responses = {}
      this.stats = {
        total_questions: 0,
        answered: 0,
        confirmed: 0,
        completion_percentage: 0
      }
      this.prd = null
      this.prdHtml = ''
      this.loading = false
      this.loadingAction = null
      this.error = null
      this.toast = null
      this.activeTab = 'context'
      this.activeSection = null
    }
  }
})
