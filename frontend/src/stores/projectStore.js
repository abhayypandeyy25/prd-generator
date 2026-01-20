import { defineStore } from 'pinia'
import { projectsApi, contextApi, questionsApi, prdApi } from '../services/api'

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
    }
  },

  actions: {
    showToast(message, type = 'info') {
      this.toast = { message, type }
      setTimeout(() => {
        this.toast = null
      }, 3000)
    },

    // Projects
    async fetchProjects() {
      try {
        const response = await projectsApi.list()
        this.projects = response.data
      } catch (error) {
        console.error('Failed to fetch projects:', error)
        this.error = 'Failed to load projects'
      }
    },

    async createProject(name) {
      try {
        const response = await projectsApi.create(name)
        this.projects.unshift(response.data)
        this.currentProject = response.data
        this.showToast('Project created successfully', 'success')
        return response.data
      } catch (error) {
        console.error('Failed to create project:', error)
        this.showToast('Failed to create project', 'error')
        throw error
      }
    },

    async selectProject(projectId) {
      const project = this.projects.find(p => p.id === projectId)
      if (project) {
        this.currentProject = project
        // Load project data
        await Promise.all([
          this.fetchContextFiles(),
          this.fetchResponses(),
          this.fetchStats()
        ])
      }
    },

    async deleteProject(projectId) {
      try {
        await projectsApi.delete(projectId)
        this.projects = this.projects.filter(p => p.id !== projectId)
        if (this.currentProject?.id === projectId) {
          this.currentProject = this.projects[0] || null
        }
        this.showToast('Project deleted', 'success')
      } catch (error) {
        this.showToast('Failed to delete project', 'error')
      }
    },

    // Context
    async uploadFiles(files) {
      if (!this.currentProject) return

      this.loading = true
      try {
        const response = await contextApi.upload(this.currentProject.id, files)
        await this.fetchContextFiles()

        if (response.data.errors?.length > 0) {
          this.showToast(`Uploaded with ${response.data.errors.length} errors`, 'warning')
        } else {
          this.showToast(`${response.data.uploaded.length} files uploaded`, 'success')
        }
        return response.data
      } catch (error) {
        this.showToast('Failed to upload files', 'error')
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchContextFiles() {
      if (!this.currentProject) return

      try {
        const response = await contextApi.list(this.currentProject.id)
        this.contextFiles = response.data
      } catch (error) {
        console.error('Failed to fetch context files:', error)
      }
    },

    async deleteContextFile(fileId) {
      try {
        await contextApi.delete(fileId)
        this.contextFiles = this.contextFiles.filter(f => f.id !== fileId)
        this.showToast('File deleted', 'success')
      } catch (error) {
        this.showToast('Failed to delete file', 'error')
      }
    },

    async fetchAggregatedContext() {
      if (!this.currentProject) return

      try {
        const response = await contextApi.getText(this.currentProject.id)
        this.aggregatedContext = response.data.text
      } catch (error) {
        console.error('Failed to fetch context:', error)
      }
    },

    // Questions
    async fetchQuestions() {
      try {
        const response = await questionsApi.getAll()
        this.questions = response.data
        if (this.questions.sections?.length > 0) {
          this.activeSection = this.questions.sections[0].id
        }
      } catch (error) {
        console.error('Failed to fetch questions:', error)
      }
    },

    async prefillQuestions() {
      if (!this.currentProject) return

      this.loading = true
      try {
        const response = await questionsApi.prefill(this.currentProject.id)
        await this.fetchResponses()
        await this.fetchStats()
        this.showToast(response.data.message, 'success')
        return response.data
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to prefill questions'
        this.showToast(message, 'error')
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchResponses() {
      if (!this.currentProject) return

      try {
        const response = await questionsApi.getResponses(this.currentProject.id)
        // Convert array to object keyed by question_id
        this.responses = {}
        response.data.forEach(r => {
          this.responses[r.question_id] = r
        })
      } catch (error) {
        console.error('Failed to fetch responses:', error)
      }
    },

    async saveResponse(questionId, response, confirmed = false) {
      if (!this.currentProject) return

      try {
        const data = {
          response,
          confirmed,
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
        this.showToast('Failed to save response', 'error')
      }
    },

    async confirmResponse(questionId, confirmed = true) {
      if (!this.currentProject) return

      try {
        await questionsApi.confirmResponse(this.currentProject.id, questionId, confirmed)
        if (this.responses[questionId]) {
          this.responses[questionId].confirmed = confirmed
        }
        await this.fetchStats()
      } catch (error) {
        this.showToast('Failed to confirm response', 'error')
      }
    },

    async fetchStats() {
      if (!this.currentProject) return

      try {
        const response = await questionsApi.getStats(this.currentProject.id)
        this.stats = response.data
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      }
    },

    // PRD
    async generatePRD() {
      if (!this.currentProject) return

      this.loading = true
      try {
        const response = await prdApi.generate(this.currentProject.id)
        this.prd = response.data.content
        this.showToast('PRD generated successfully', 'success')
        return response.data
      } catch (error) {
        const message = error.response?.data?.error || 'Failed to generate PRD'
        this.showToast(message, 'error')
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchPRD() {
      if (!this.currentProject) return

      try {
        const response = await prdApi.get(this.currentProject.id)
        this.prd = response.data.content_md
      } catch (error) {
        // PRD might not exist yet
        this.prd = null
      }
    },

    async fetchPRDPreview() {
      if (!this.currentProject) return

      try {
        const response = await prdApi.preview(this.currentProject.id)
        this.prd = response.data.markdown
        this.prdHtml = response.data.html
      } catch (error) {
        this.prd = null
        this.prdHtml = ''
      }
    },

    async exportPRD(format) {
      if (!this.currentProject) return

      try {
        let response
        let filename

        if (format === 'md') {
          response = await prdApi.exportMarkdown(this.currentProject.id)
          filename = `PRD_${this.currentProject.name}.md`
        } else {
          response = await prdApi.exportDocx(this.currentProject.id)
          filename = `PRD_${this.currentProject.name}.docx`
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
        this.showToast('Failed to export PRD', 'error')
      }
    },

    setActiveTab(tab) {
      this.activeTab = tab
    },

    setActiveSection(sectionId) {
      this.activeSection = sectionId
    }
  }
})
