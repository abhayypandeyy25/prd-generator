<template>
  <div class="home-tab">
    <!-- Projects Section -->
    <div class="section">
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Projects</h3>
          <button class="btn btn-primary" @click="$emit('create-project')">
            + New Project
          </button>
        </div>
        <div class="card-body">
          <!-- Empty State -->
          <div v-if="store.projects.length === 0" class="empty-state">
            <div class="empty-icon">📋</div>
            <h4>No Projects Yet</h4>
            <p>Create your first project to start building PRDs with AI assistance.</p>
            <button class="btn btn-primary" @click="$emit('create-project')">
              Create Your First Project
            </button>
          </div>

          <!-- Projects List -->
          <div v-else class="projects-grid">
            <div
              v-for="project in store.projects"
              :key="project.id"
              class="project-card"
              :class="{ active: store.currentProject?.id === project.id }"
              @click="selectProject(project)"
            >
              <div class="project-header">
                <h4 class="project-name">{{ project.name }}</h4>
                <button
                  class="btn-icon delete-btn"
                  @click.stop="confirmDelete(project)"
                  title="Delete project"
                >
                  🗑️
                </button>
              </div>
              <div class="project-meta">
                <span class="project-date">
                  Created {{ formatDate(project.created_at) }}
                </span>
                <span v-if="getProjectFeatureCount(project.id) > 0" class="feature-count">
                  {{ getProjectFeatureCount(project.id) }} features
                </span>
              </div>
              <div class="project-actions">
                <button
                  class="btn btn-secondary btn-sm"
                  @click.stop="openProject(project)"
                >
                  Open Project
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Parking Lot Section -->
    <div class="section">
      <div class="card parking-lot-card">
        <div class="card-header" @click="showParkingLot = !showParkingLot" style="cursor: pointer;">
          <div class="header-left">
            <h3 class="card-title">Parking Lot</h3>
            <span class="section-badge">{{ totalParkingLotCount }} features</span>
          </div>
          <span class="toggle-icon">{{ showParkingLot ? '▼' : '▶' }}</span>
        </div>
        <div v-if="showParkingLot" class="card-body">
          <p class="section-description">
            Features that have been deselected across all projects. These can be re-activated from each project's Features tab.
          </p>

          <!-- Empty Parking Lot -->
          <div v-if="totalParkingLotCount === 0" class="empty-state-small">
            <p>No parked features yet. Features you deselect in your projects will appear here.</p>
          </div>

          <!-- Parking Lot by Project -->
          <div v-else class="parking-lot-list">
            <div
              v-for="project in projectsWithParkingLot"
              :key="project.id"
              class="parking-lot-project"
            >
              <div class="parking-project-header">
                <h4 class="parking-project-name">{{ project.name }}</h4>
                <span class="parking-count">{{ project.parkingLotFeatures.length }} parked</span>
              </div>
              <div class="parking-features">
                <div
                  v-for="feature in project.parkingLotFeatures"
                  :key="feature.id"
                  class="parking-feature-item"
                >
                  <div class="feature-info">
                    <span class="feature-name">{{ feature.name }}</span>
                    <span v-if="feature.is_ai_generated" class="ai-badge">AI</span>
                  </div>
                  <p class="feature-description">{{ feature.description || 'No description' }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="projectToDelete" class="modal-overlay" @click.self="projectToDelete = null">
      <div class="modal">
        <h3 style="margin-bottom: 1rem;">Delete Project?</h3>
        <p style="color: var(--gray-600); margin-bottom: 1.5rem;">
          Are you sure you want to delete <strong>{{ projectToDelete.name }}</strong>?
          This will also delete all context files, responses, and generated PRDs.
          This action cannot be undone.
        </p>
        <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
          <button class="btn btn-secondary" @click="projectToDelete = null">Cancel</button>
          <button class="btn btn-danger" @click="deleteProject">
            Delete Project
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import { featuresApi } from '../services/api'

const store = useProjectStore()
const projectToDelete = ref(null)
const showParkingLot = ref(true)
const allProjectFeatures = ref({}) // { projectId: [features] }

const emit = defineEmits(['create-project', 'project-selected'])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  if (diffDays < 7) return `${diffDays} days ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
  })
}

const selectProject = async (project) => {
  await store.selectProject(project.id)
  emit('project-selected', project)
}

const openProject = async (project) => {
  await store.selectProject(project.id)
  store.setActiveTab('context')
  emit('project-selected', project)
}

const confirmDelete = (project) => {
  projectToDelete.value = project
}

const deleteProject = async () => {
  if (!projectToDelete.value) return

  try {
    await store.deleteProject(projectToDelete.value.id)
    projectToDelete.value = null
  } catch (error) {
    console.error('Failed to delete project:', error)
  }
}

// Fetch features for all projects to show parking lot
const fetchAllProjectFeatures = async () => {
  for (const project of store.projects) {
    try {
      const response = await featuresApi.list(project.id)
      allProjectFeatures.value[project.id] = Array.isArray(response.data) ? response.data : []
    } catch (error) {
      console.error(`Failed to fetch features for project ${project.id}:`, error)
      allProjectFeatures.value[project.id] = []
    }
  }
}

// Get feature count for a project
const getProjectFeatureCount = (projectId) => {
  const features = allProjectFeatures.value[projectId] || []
  return features.filter(f => f.is_selected).length
}

// Get parking lot features for all projects
const projectsWithParkingLot = computed(() => {
  return store.projects
    .map(project => ({
      ...project,
      parkingLotFeatures: (allProjectFeatures.value[project.id] || []).filter(f => !f.is_selected)
    }))
    .filter(project => project.parkingLotFeatures.length > 0)
})

// Total parking lot count
const totalParkingLotCount = computed(() => {
  return projectsWithParkingLot.value.reduce((sum, p) => sum + p.parkingLotFeatures.length, 0)
})

onMounted(() => {
  fetchAllProjectFeatures()
})
</script>

<style scoped>
.home-tab {
  max-width: 1000px;
  margin: 0 auto;
}

.section {
  margin-bottom: 2rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-badge {
  background: var(--gray-200);
  color: var(--gray-600);
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
}

.toggle-icon {
  color: var(--gray-400);
  font-size: 0.75rem;
}

.section-description {
  color: var(--gray-500);
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h4 {
  margin-bottom: 0.5rem;
  color: var(--gray-700);
}

.empty-state p {
  color: var(--gray-500);
  margin-bottom: 1.5rem;
}

.empty-state-small {
  text-align: center;
  padding: 2rem;
  background: var(--gray-50);
  border-radius: var(--radius);
  color: var(--gray-500);
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.project-card {
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.project-card:hover {
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.project-card.active {
  border-color: var(--primary);
  background: var(--primary-light, #f0f7ff);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.project-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
  word-break: break-word;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  font-size: 0.875rem;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.btn-icon:hover {
  opacity: 1;
}

.delete-btn:hover {
  opacity: 1;
}

.project-meta {
  margin-bottom: 1rem;
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.project-date {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.feature-count {
  font-size: 0.75rem;
  color: var(--primary);
  background: var(--primary-light, #e0f2fe);
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
}

.project-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
}

.btn-danger {
  background: var(--red-500, #ef4444);
  color: white;
  border: none;
}

.btn-danger:hover {
  background: var(--red-600, #dc2626);
}

/* Parking Lot Styles */
.parking-lot-card {
  background: var(--gray-50);
  border: 1px dashed var(--gray-300);
}

.parking-lot-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.parking-lot-project {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 1rem;
}

.parking-project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--gray-100);
}

.parking-project-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--gray-700);
  margin: 0;
}

.parking-count {
  font-size: 0.75rem;
  color: var(--gray-500);
  background: var(--gray-100);
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
}

.parking-features {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.parking-feature-item {
  padding: 0.5rem;
  background: var(--gray-50);
  border-radius: var(--radius);
}

.feature-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.feature-name {
  font-weight: 500;
  color: var(--gray-700);
  font-size: 0.875rem;
}

.ai-badge {
  background: var(--primary-light, #e0f2fe);
  color: var(--primary, #0284c7);
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  text-transform: uppercase;
}

.feature-description {
  color: var(--gray-500);
  font-size: 0.8125rem;
  margin: 0;
  line-height: 1.4;
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
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
}
</style>
