<template>
  <div class="stakeholder-view">
    <!-- Role Selector -->
    <div class="role-selector">
      <h3>Select Stakeholder View</h3>
      <p class="description">Choose a role to see a customized view of the PRD</p>

      <div class="roles-grid">
        <div
          v-for="profile in profiles"
          :key="profile.id"
          class="role-card"
          :class="{ active: selectedRole === profile.id }"
          @click="selectRole(profile.id)"
        >
          <span class="role-icon">{{ profile.icon }}</span>
          <span class="role-name">{{ profile.name }}</span>
          <span class="role-focus">{{ profile.focus_areas?.slice(0, 3).join(', ') }}</span>
        </div>
      </div>
    </div>

    <!-- Content View -->
    <div v-if="selectedRole" class="content-section">
      <div class="content-header">
        <div class="header-info">
          <span class="view-icon">{{ currentProfile?.icon }}</span>
          <h4>{{ currentProfile?.name }} View</h4>
        </div>
        <div class="header-actions">
          <button
            class="btn btn-secondary btn-sm"
            @click="generateSummary"
            :disabled="summaryLoading"
          >
            {{ summaryLoading ? 'Generating...' : '✨ Generate Summary' }}
          </button>
          <button class="btn btn-secondary btn-sm" @click="copyContent">
            📋 Copy
          </button>
          <button class="btn btn-secondary btn-sm" @click="selectedRole = null">
            ← Back
          </button>
        </div>
      </div>

      <!-- Focus Areas -->
      <div class="focus-areas">
        <span class="focus-label">Focus Areas:</span>
        <span
          v-for="area in currentProfile?.focus_areas"
          :key="area"
          class="focus-tag"
        >
          {{ area }}
        </span>
      </div>

      <!-- Summary (if generated) -->
      <div v-if="summary" class="summary-section">
        <div class="summary-header">
          <h5>Executive Summary for {{ currentProfile?.name }}</h5>
          <button class="btn btn-sm btn-ghost" @click="summary = null">
            Hide Summary
          </button>
        </div>
        <div class="summary-content" v-html="renderedSummary"></div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading {{ currentProfile?.name }} view...</p>
      </div>

      <!-- Filtered PRD Content -->
      <div v-else-if="filteredContent" class="prd-content" v-html="renderedContent"></div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <p>No PRD content available for this view.</p>
      </div>
    </div>

    <!-- Default State -->
    <div v-else class="default-state">
      <div class="default-icon">👥</div>
      <h4>Stakeholder Views</h4>
      <p>Select a role above to see a customized view of the PRD tailored to their needs.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { stakeholderApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()

const profiles = ref([])
const selectedRole = ref(null)
const filteredContent = ref('')
const summary = ref(null)
const loading = ref(false)
const summaryLoading = ref(false)

const currentProfile = computed(() => {
  return profiles.value.find(p => p.id === selectedRole.value)
})

const renderedContent = computed(() => {
  if (!filteredContent.value) return ''
  return marked(filteredContent.value)
})

const renderedSummary = computed(() => {
  if (!summary.value) return ''
  return marked(summary.value)
})

onMounted(async () => {
  try {
    const response = await stakeholderApi.getProfiles()
    profiles.value = response.data.profiles || []
  } catch (error) {
    console.error('Failed to load profiles:', error)
  }
})

const selectRole = async (role) => {
  if (!store.currentProject?.id) return

  selectedRole.value = role
  loading.value = true
  summary.value = null

  try {
    const response = await stakeholderApi.getView(store.currentProject.id, role)
    filteredContent.value = response.data.content || ''
  } catch (error) {
    console.error('Failed to load stakeholder view:', error)
    store.showToast('Failed to load view', 'error')
    filteredContent.value = ''
  } finally {
    loading.value = false
  }
}

const generateSummary = async () => {
  if (!store.currentProject?.id || !selectedRole.value) return

  summaryLoading.value = true
  try {
    const response = await stakeholderApi.generateSummary(
      store.currentProject.id,
      selectedRole.value
    )
    summary.value = response.data.summary
    store.showToast('Summary generated', 'success')
  } catch (error) {
    console.error('Failed to generate summary:', error)
    store.showToast('Failed to generate summary', 'error')
  } finally {
    summaryLoading.value = false
  }
}

const copyContent = async () => {
  const content = summary.value || filteredContent.value
  if (!content) return

  try {
    await navigator.clipboard.writeText(content)
    store.showToast('Copied to clipboard', 'success')
  } catch (error) {
    store.showToast('Failed to copy', 'error')
  }
}
</script>

<style scoped>
.stakeholder-view {
  height: 100%;
}

.role-selector {
  margin-bottom: 1.5rem;
}

.role-selector h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  color: var(--gray-800);
}

.description {
  margin: 0 0 1rem 0;
  color: var(--gray-500);
  font-size: 0.875rem;
}

.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}

.role-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: white;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.role-card:hover {
  border-color: var(--primary);
  background: var(--primary-light);
}

.role-card.active {
  border-color: var(--primary);
  background: var(--primary-light);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.role-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.role-name {
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 0.25rem;
}

.role-focus {
  font-size: 0.75rem;
  color: var(--gray-500);
  line-height: 1.3;
}

.content-section {
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.view-icon {
  font-size: 1.5rem;
}

.header-info h4 {
  margin: 0;
  color: var(--gray-800);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.focus-areas {
  padding: 0.75rem 1.5rem;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.focus-label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
  font-weight: 600;
}

.focus-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: 9999px;
  color: var(--gray-600);
}

.summary-section {
  padding: 1.5rem;
  background: linear-gradient(135deg, #f0f9ff 0%, #f5f3ff 100%);
  border-bottom: 1px solid var(--gray-200);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.summary-header h5 {
  margin: 0;
  color: var(--gray-700);
  font-size: 0.9375rem;
}

.btn-ghost {
  background: none;
  border: none;
  color: var(--gray-500);
  padding: 0.25rem 0.5rem;
  cursor: pointer;
}

.btn-ghost:hover {
  color: var(--gray-700);
}

.summary-content {
  font-size: 0.9375rem;
  line-height: 1.6;
  color: var(--gray-700);
}

.summary-content :deep(h1),
.summary-content :deep(h2),
.summary-content :deep(h3) {
  margin-top: 1.25rem;
  margin-bottom: 0.75rem;
  color: var(--gray-800);
}

.summary-content :deep(ul),
.summary-content :deep(ol) {
  padding-left: 1.25rem;
}

.summary-content :deep(li) {
  margin-bottom: 0.375rem;
}

.prd-content {
  padding: 2rem;
  max-height: 60vh;
  overflow-y: auto;
}

.prd-content :deep(h1) {
  font-size: 1.75rem;
  margin-bottom: 1.5rem;
  color: var(--gray-900);
  border-bottom: 2px solid var(--primary);
  padding-bottom: 0.5rem;
}

.prd-content :deep(h2) {
  font-size: 1.375rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
  color: var(--gray-800);
}

.prd-content :deep(h3) {
  font-size: 1.125rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: var(--gray-700);
}

.prd-content :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.7;
}

.prd-content :deep(ul),
.prd-content :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.prd-content :deep(li) {
  margin-bottom: 0.5rem;
}

.prd-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
}

.prd-content :deep(th),
.prd-content :deep(td) {
  padding: 0.75rem;
  border: 1px solid var(--gray-200);
  text-align: left;
}

.prd-content :deep(th) {
  background: var(--gray-50);
  font-weight: 600;
}

.loading-state {
  padding: 3rem;
  text-align: center;
}

.empty-state,
.default-state {
  padding: 3rem;
  text-align: center;
  color: var(--gray-500);
}

.default-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.default-state h4 {
  margin: 0 0 0.5rem 0;
  color: var(--gray-700);
}

.default-state p {
  margin: 0;
  max-width: 400px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .roles-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .content-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
