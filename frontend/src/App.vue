<template>
  <div class="app-container">
    <!-- Header -->
    <header class="app-header">
      <h1 class="app-title">PM <span>Clarity</span></h1>

      <div class="project-selector">
        <select v-model="selectedProjectId" @change="onProjectChange">
          <option value="">Select a project...</option>
          <option v-for="project in store.projects" :key="project.id" :value="project.id">
            {{ project.name }}
          </option>
        </select>
        <button class="btn btn-primary" @click="showNewProjectModal = true">
          + New Project
        </button>
      </div>
    </header>

    <!-- Tab Navigation -->
    <nav class="tab-navigation" v-if="store.currentProject">
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
        :class="{ active: store.activeTab === 'questions' }"
        @click="store.setActiveTab('questions')"
      >
        2. Questions
        <span class="tab-badge">{{ store.stats.confirmed }}/{{ store.stats.total_questions }}</span>
      </button>
      <button
        class="tab-btn"
        :class="{ active: store.activeTab === 'prd' }"
        @click="store.setActiveTab('prd')"
      >
        3. PRD
      </button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <!-- No Project Selected -->
      <div v-if="!store.currentProject" class="card">
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

      <!-- Tab Content -->
      <template v-else>
        <ContextTab v-if="store.activeTab === 'context'" />
        <QuestionsTab v-if="store.activeTab === 'questions'" />
        <PRDTab v-if="store.activeTab === 'prd'" />
      </template>
    </main>

    <!-- New Project Modal -->
    <div v-if="showNewProjectModal" class="modal-overlay" @click.self="showNewProjectModal = false">
      <div class="modal">
        <h3 style="margin-bottom: 1rem;">Create New Project</h3>
        <input
          v-model="newProjectName"
          type="text"
          placeholder="Project name (e.g., User Analytics Dashboard)"
          style="width: 100%; padding: 0.75rem; border: 1px solid var(--gray-300); border-radius: var(--radius); margin-bottom: 1rem;"
          @keyup.enter="createProject"
        >
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <button class="btn btn-secondary" @click="showNewProjectModal = false">Cancel</button>
          <button class="btn btn-primary" @click="createProject" :disabled="!newProjectName.trim()">
            Create Project
          </button>
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
import { ref, onMounted, watch } from 'vue'
import { useProjectStore } from './stores/projectStore'
import ContextTab from './components/ContextTab.vue'
import QuestionsTab from './components/QuestionsTab.vue'
import PRDTab from './components/PRDTab.vue'

const store = useProjectStore()

const selectedProjectId = ref('')
const showNewProjectModal = ref(false)
const newProjectName = ref('')

onMounted(async () => {
  await store.fetchProjects()
  await store.fetchQuestions()

  // Select first project if available
  if (store.projects.length > 0) {
    selectedProjectId.value = store.projects[0].id
    await store.selectProject(selectedProjectId.value)
  }
})

const onProjectChange = async () => {
  if (selectedProjectId.value) {
    await store.selectProject(selectedProjectId.value)
  }
}

const createProject = async () => {
  if (!newProjectName.value.trim()) return

  try {
    const project = await store.createProject(newProjectName.value.trim())
    selectedProjectId.value = project.id
    showNewProjectModal.value = false
    newProjectName.value = ''
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
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
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
</style>
