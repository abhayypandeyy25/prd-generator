<template>
  <!-- Show AuthPage if not authenticated -->
  <AuthPage v-if="!authStore.isAuthenticated && !authStore.loading" />

  <!-- Show loading screen while checking auth -->
  <div v-else-if="authStore.loading" class="loading-screen">
    <div class="spinner"></div>
    <p>Loading PM Clarity...</p>
  </div>

  <!-- Show main app if authenticated -->
  <div v-else class="app-container">
    <!-- Header -->
    <header class="app-header">
      <div class="header-left">
        <h1 class="app-title" @click="goHome" style="cursor: pointer;">PM <span>Clarity</span></h1>
        <button class="btn btn-ghost home-btn" @click="goHome" title="Go to Home">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
          Home
        </button>
      </div>

      <div class="header-right">
        <span class="user-info">{{ authStore.userDisplayName }}</span>
        <button class="btn btn-secondary" @click="showAnalytics = !showAnalytics">
          📊 Analytics
        </button>
        <button class="btn btn-primary" @click="showNewProjectModal = true">
          + New Project
        </button>
        <button class="btn btn-ghost" @click="handleLogout" title="Logout">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </header>

    <!-- Project Context Bar (only when project selected) -->
    <div v-if="store.currentProject" class="project-bar">
      <div class="project-info">
        <span class="project-label">Working on:</span>
        <select v-model="selectedProjectId" @change="onProjectChange" class="project-select">
          <option v-for="project in store.projects" :key="project.id" :value="project.id">
            {{ project.name }}
          </option>
        </select>
      </div>

      <!-- Tab Navigation -->
      <nav class="tab-navigation">
        <button
          class="tab-btn"
          :class="{ active: store.activeTab === 'context' }"
          @click="store.setActiveTab('context')"
        >
          1. Context
          <span class="tab-badge">{{ store.contextFiles.length }}</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: store.activeTab === 'features' }"
          @click="store.setActiveTab('features')"
        >
          2. Features
          <span class="tab-badge">{{ store.activeFeatureCount }}</span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: store.activeTab === 'questions' }"
          @click="store.setActiveTab('questions')"
        >
          3. Questions
          <span class="tab-badge" :class="{ 'badge-warning': confirmationPercentage < 50, 'badge-success': confirmationPercentage >= 80 }">
            {{ store.stats.confirmed }}/{{ store.stats.total_questions }}
          </span>
        </button>
        <button
          class="tab-btn"
          :class="{ active: store.activeTab === 'prd' }"
          @click="store.setActiveTab('prd')"
        >
          4. PRD
        </button>
      </nav>
    </div>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Projects Tab (Home) -->
      <ProjectsTab
        v-if="store.activeTab === 'projects'"
        @create-project="showNewProjectModal = true"
        @project-selected="onProjectSelected"
      />

      <!-- No Project Selected (when not on projects tab) -->
      <div v-else-if="!store.currentProject" class="card">
        <div class="card-body" style="text-align: center; padding: 4rem;">
          <h2 style="margin-bottom: 1rem;">Welcome to PM Clarity</h2>
          <p style="color: var(--gray-500); margin-bottom: 2rem;">
            Get complete clarity on your product idea before writing your PRD.<br>
            Select an existing project or create a new one to get started.
          </p>
          <button class="btn btn-primary" @click="showNewProjectModal = true">
            Create Your First Project
          </button>
        </div>
      </div>

      <!-- Analytics Dashboard (Modal) -->
      <div v-if="showAnalytics" class="analytics-modal" @click.self="showAnalytics = false">
        <div class="analytics-content">
          <button class="close-btn" @click="showAnalytics = false">✕</button>
          <AnalyticsDashboard />
        </div>
      </div>

      <!-- Tab Content -->
      <template v-else>
        <ContextTab v-if="store.activeTab === 'context'" />
        <FeaturesTab v-if="store.activeTab === 'features'" />
        <QuestionsTab v-if="store.activeTab === 'questions'" />
        <PRDTab v-if="store.activeTab === 'prd'" />
      </template>
    </main>

    <!-- New Project Modal -->
    <div v-if="showNewProjectModal" class="modal-overlay" @click.self="closeNewProjectModal">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>Create New Project</h3>
          <button class="close-btn" @click="closeNewProjectModal">×</button>
        </div>

        <div class="modal-body">
          <!-- Step 1: Project Name -->
          <div v-if="createProjectStep === 1">
            <div class="form-group">
              <label>Project Name</label>
              <input
                v-model="newProjectName"
                type="text"
                class="form-input"
                placeholder="e.g., User Analytics Dashboard"
                @keyup.enter="nextStep"
              >
            </div>
            <p class="hint">Give your project a descriptive name that reflects its purpose.</p>
          </div>

          <!-- Step 2: Template Selection -->
          <div v-else-if="createProjectStep === 2">
            <TemplateSelector
              :selected-id="selectedTemplateId"
              @select="onTemplateSelect"
            />
          </div>
        </div>

        <div class="modal-footer">
          <div class="step-indicator">
            Step {{ createProjectStep }} of 2
          </div>
          <div class="modal-actions">
            <button v-if="createProjectStep > 1" class="btn btn-secondary" @click="prevStep">
              Back
            </button>
            <button class="btn btn-secondary" @click="closeNewProjectModal">Cancel</button>
            <button
              v-if="createProjectStep === 1"
              class="btn btn-primary"
              @click="nextStep"
              :disabled="!newProjectName.trim()"
            >
              Next: Choose Template
            </button>
            <button
              v-else
              class="btn btn-primary"
              @click="createProject"
              :disabled="!newProjectName.trim()"
            >
              Create Project
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div v-if="store.toast" :class="['toast', store.toast.type]">
      {{ store.toast.message }}
    </div>

    <!-- Loading Overlay -->
    <div v-if="store.loading" class="loading-overlay">
      <div class="spinner"></div>
      <p style="margin-top: 1rem;">Processing...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useProjectStore } from './stores/projectStore'
import { useAuthStore } from './stores/authStore'
import AuthPage from './components/AuthPage.vue'
import ProjectsTab from './components/ProjectsTab.vue'
import ContextTab from './components/ContextTab.vue'
import FeaturesTab from './components/FeaturesTab.vue'
import QuestionsTab from './components/QuestionsTab.vue'
import PRDTab from './components/PRDTab.vue'
import TemplateSelector from './components/TemplateSelector.vue'
import AnalyticsDashboard from './components/AnalyticsDashboard.vue'

const store = useProjectStore()
const authStore = useAuthStore()

const selectedProjectId = ref('')
const showNewProjectModal = ref(false)
const showAnalytics = ref(false)
const newProjectName = ref('')
const createProjectStep = ref(1)
const selectedTemplateId = ref(null)
const selectedTemplate = ref(null)

const confirmationPercentage = computed(() => {
  if (!store.stats.total_questions) return 0
  return Math.round((store.stats.confirmed / store.stats.total_questions) * 100)
})

onMounted(async () => {
  // Initialize authentication first
  await authStore.initialize()

  // Load data only if authenticated
  if (authStore.isAuthenticated) {
    await loadData()
  }
})

const loadData = async () => {
  await store.fetchProjects()
  await store.fetchQuestions()
  await store.fetchTemplates()

  // Don't auto-select, start on home page
  store.setActiveTab('projects')
}

const handleLogout = async () => {
  await authStore.signOut()
  // Clear project store data
  store.$reset()
}

const goHome = () => {
  store.setActiveTab('projects')
}

const onProjectChange = async () => {
  if (selectedProjectId.value) {
    await store.selectProject(selectedProjectId.value)
  }
}

const onProjectSelected = (project) => {
  selectedProjectId.value = project.id
}

const onTemplateSelect = (template) => {
  selectedTemplateId.value = template.id
  selectedTemplate.value = template
  store.setSelectedTemplate(template)
}

const nextStep = () => {
  if (createProjectStep.value < 2) {
    createProjectStep.value++
  }
}

const prevStep = () => {
  if (createProjectStep.value > 1) {
    createProjectStep.value--
  }
}

const closeNewProjectModal = () => {
  showNewProjectModal.value = false
  newProjectName.value = ''
  createProjectStep.value = 1
  selectedTemplateId.value = null
  selectedTemplate.value = null
}

const createProject = async () => {
  if (!newProjectName.value.trim()) return

  try {
    const project = await store.createProject(newProjectName.value.trim())
    selectedProjectId.value = project.id
    closeNewProjectModal()
  } catch (error) {
    console.error('Failed to create project:', error)
  }
}

watch(() => store.currentProject, (project) => {
  if (project) {
    selectedProjectId.value = project.id
  }
})
</script>

<style scoped>
.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.home-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: var(--gray-600);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius);
  transition: all 0.2s;
}

.home-btn:hover {
  background: var(--gray-100);
  color: var(--primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.project-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 2rem;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
  gap: 1rem;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.project-label {
  font-size: 0.875rem;
  color: var(--gray-500);
  white-space: nowrap;
}

.project-select {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--gray-900);
  background: white;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  padding: 0.375rem 2rem 0.375rem 0.75rem;
  cursor: pointer;
  max-width: 250px;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.25em 1.25em;
}

.project-select:hover {
  border-color: var(--primary);
}

.tab-navigation {
  display: flex;
  gap: 0.25rem;
}

.badge-warning {
  background: var(--warning) !important;
  color: #92400e !important;
}

.badge-success {
  background: var(--success) !important;
  color: #065f46 !important;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-lg {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--gray-200);
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  font-size: 1.5rem;
  color: var(--gray-500);
  cursor: pointer;
  border-radius: var(--radius);
}

.close-btn:hover {
  background: var(--gray-100);
}

.modal-body {
  padding: 1.5rem;
  max-height: 60vh;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.step-indicator {
  font-size: 0.875rem;
  color: var(--gray-500);
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.375rem;
  font-weight: 500;
  color: var(--gray-700);
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 0.9375rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.hint {
  font-size: 0.875rem;
  color: var(--gray-500);
  margin-top: 0.5rem;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

/* Analytics Modal */
.analytics-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.analytics-content {
  background: white;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  position: relative;
}

.analytics-content .close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--gray-500);
}

.analytics-content .close-btn:hover {
  background: var(--gray-100);
  color: var(--gray-700);
}

/* Loading Screen */
.loading-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
  color: white;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-screen p {
  font-size: 1.125rem;
  opacity: 0.9;
}

/* User Info */
.user-info {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  background: var(--gray-50);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  color: var(--gray-700);
  margin-right: 0.5rem;
}

.btn-ghost {
  background: transparent;
  border: none;
  color: var(--gray-600);
  padding: 0.5rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ghost:hover {
  background: var(--gray-100);
  color: var(--gray-900);
}
</style>
