<template>
  <div class="analytics-dashboard">
    <h2>Analytics & Insights</h2>

    <!-- Overview Tab / Project Tab Toggle -->
    <div class="tab-selector">
      <button
        class="tab-btn"
        :class="{ active: activeView === 'overview' }"
        @click="activeView = 'overview'"
      >
        📊 Overview
      </button>
      <button
        v-if="store.currentProject"
        class="tab-btn"
        :class="{ active: activeView === 'project' }"
        @click="activeView = 'project'"
      >
        📈 Current Project
      </button>
    </div>

    <!-- Overview Analytics -->
    <div v-if="activeView === 'overview' && overviewData" class="overview-section">
      <!-- Summary Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📁</div>
          <div class="stat-content">
            <span class="stat-value">{{ overviewData.summary.total_projects }}</span>
            <span class="stat-label">Total Projects</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">📄</div>
          <div class="stat-content">
            <span class="stat-value">{{ overviewData.summary.prds_generated }}</span>
            <span class="stat-label">PRDs Generated</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">📚</div>
          <div class="stat-content">
            <span class="stat-value">{{ overviewData.summary.total_context_files }}</span>
            <span class="stat-label">Context Files</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <span class="stat-value">{{ overviewData.summary.confirmed_responses }}</span>
            <span class="stat-label">Confirmed Responses</span>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="section-card">
        <h3>Recent Activity (Last 7 Days)</h3>
        <div class="activity-grid">
          <div class="activity-item">
            <span class="activity-label">New Projects</span>
            <span class="activity-value">{{ overviewData.recent_activity.projects_last_7_days }}</span>
          </div>
          <div class="activity-item">
            <span class="activity-label">PRDs Generated</span>
            <span class="activity-value">{{ overviewData.recent_activity.prds_last_7_days }}</span>
          </div>
        </div>
      </div>

      <!-- Averages -->
      <div class="section-card">
        <h3>Averages Per Project</h3>
        <div class="averages-grid">
          <div class="avg-item">
            <div class="avg-icon">📁</div>
            <div class="avg-content">
              <span class="avg-value">{{ overviewData.averages.context_files_per_project }}</span>
              <span class="avg-label">Context Files</span>
            </div>
          </div>
          <div class="avg-item">
            <div class="avg-icon">💬</div>
            <div class="avg-content">
              <span class="avg-value">{{ overviewData.averages.responses_per_project }}</span>
              <span class="avg-label">Responses</span>
            </div>
          </div>
          <div class="avg-item">
            <div class="avg-icon">⏱️</div>
            <div class="avg-content">
              <span class="avg-value">{{ overviewData.averages.hours_per_project }}h</span>
              <span class="avg-label">Time Spent</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Efficiency Metrics -->
      <div class="section-card">
        <h3>Efficiency Metrics</h3>
        <div class="efficiency-grid">
          <div class="efficiency-item">
            <span class="efficiency-label">AI Assistance Rate</span>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: overviewData.efficiency.ai_assistance_rate + '%' }"></div>
            </div>
            <span class="efficiency-value">{{ overviewData.efficiency.ai_assistance_rate }}%</span>
          </div>
          <div class="efficiency-item">
            <span class="efficiency-label">Confirmation Rate</span>
            <div class="progress-bar">
              <div class="progress-fill success" :style="{ width: overviewData.efficiency.confirmation_rate + '%' }"></div>
            </div>
            <span class="efficiency-value">{{ overviewData.efficiency.confirmation_rate }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Project Analytics -->
    <div v-if="activeView === 'project' && projectData" class="project-section">
      <!-- Project Header -->
      <div class="project-header">
        <h3>{{ projectData.project_info.name }}</h3>
        <span class="time-spent">⏱️ {{ projectData.project_info.time_spent_hours }}h spent</span>
      </div>

      <!-- Completion Progress -->
      <div class="section-card">
        <h4>Completion Progress</h4>
        <div class="completion-bar">
          <div class="completion-fill" :style="{ width: projectData.completion.percentage + '%' }"></div>
          <span class="completion-text">{{ projectData.completion.percentage }}%</span>
        </div>

        <div class="stages-list">
          <div
            v-for="(completed, stage) in projectData.completion.stages"
            :key="stage"
            class="stage-item"
            :class="{ completed }"
          >
            <span class="stage-icon">{{ completed ? '✅' : '⭕' }}</span>
            <span class="stage-label">{{ formatStageName(stage) }}</span>
          </div>
        </div>
      </div>

      <!-- Context Stats -->
      <div class="section-card">
        <h4>Context</h4>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Files Uploaded</span>
            <span class="detail-value">{{ projectData.context.files_uploaded }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Total Characters</span>
            <span class="detail-value">{{ formatNumber(projectData.context.total_characters) }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">File Types</span>
            <span class="detail-value">{{ projectData.context.file_types.join(', ') || 'None' }}</span>
          </div>
        </div>
      </div>

      <!-- Features & Questions -->
      <div class="stats-grid">
        <div class="section-card">
          <h4>Features</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Total Extracted</span>
              <span class="detail-value">{{ projectData.features.total_extracted }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Selected</span>
              <span class="detail-value highlight">{{ projectData.features.selected }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Parking Lot</span>
              <span class="detail-value">{{ projectData.features.in_parking_lot }}</span>
            </div>
          </div>
        </div>

        <div class="section-card">
          <h4>Questions</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Total Responses</span>
              <span class="detail-value">{{ projectData.questions.total_responses }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Confirmed</span>
              <span class="detail-value highlight">{{ projectData.questions.confirmed }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Confirmation Rate</span>
              <span class="detail-value">{{ projectData.questions.confirmation_rate }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- PRD Info -->
      <div class="section-card">
        <h4>PRD</h4>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Status</span>
            <span class="detail-value" :class="projectData.prd.generated ? 'success' : 'pending'">
              {{ projectData.prd.generated ? 'Generated' : 'Not Yet Generated' }}
            </span>
          </div>
          <div v-if="projectData.prd.generated" class="detail-item">
            <span class="detail-label">Version</span>
            <span class="detail-value">v{{ projectData.prd.version }}</span>
          </div>
          <div v-if="projectData.prd.generated" class="detail-item">
            <span class="detail-label">Word Count</span>
            <span class="detail-value">{{ formatNumber(projectData.prd.word_count) }}</span>
          </div>
          <div v-if="projectData.prd.generated" class="detail-item">
            <span class="detail-label">Edit History</span>
            <span class="detail-value">{{ projectData.prd.edit_history_count }}</span>
          </div>
        </div>
      </div>

      <!-- Timeline -->
      <div v-if="timeline" class="section-card">
        <h4>Project Timeline</h4>
        <div class="timeline">
          <div v-for="(event, idx) in timeline.timeline" :key="idx" class="timeline-item">
            <div class="timeline-dot" :class="event.type"></div>
            <div class="timeline-content">
              <span class="timeline-desc">{{ event.description }}</span>
              <span class="timeline-time">{{ formatDate(event.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading analytics...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { analyticsApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()

const activeView = ref('overview')
const overviewData = ref(null)
const projectData = ref(null)
const timeline = ref(null)
const loading = ref(false)

onMounted(async () => {
  await loadOverview()
  if (store.currentProject?.id) {
    await loadProjectAnalytics()
  }
})

watch(() => store.currentProject?.id, async (newId) => {
  if (newId && activeView.value === 'project') {
    await loadProjectAnalytics()
  }
})

watch(activeView, async (newView) => {
  if (newView === 'overview' && !overviewData.value) {
    await loadOverview()
  } else if (newView === 'project' && store.currentProject?.id && !projectData.value) {
    await loadProjectAnalytics()
  }
})

const loadOverview = async () => {
  loading.value = true
  try {
    const response = await analyticsApi.getOverview()
    overviewData.value = response.data
  } catch (error) {
    console.error('Failed to load overview:', error)
  } finally {
    loading.value = false
  }
}

const loadProjectAnalytics = async () => {
  if (!store.currentProject?.id) return

  loading.value = true
  try {
    const [analyticsRes, timelineRes] = await Promise.all([
      analyticsApi.getProjectAnalytics(store.currentProject.id),
      analyticsApi.getTimeline(store.currentProject.id)
    ])

    projectData.value = analyticsRes.data
    timeline.value = timelineRes.data
  } catch (error) {
    console.error('Failed to load project analytics:', error)
  } finally {
    loading.value = false
  }
}

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const formatStageName = (stage) => {
  return stage.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const formatDate = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.analytics-dashboard {
  padding: 1.5rem;
}

.analytics-dashboard h2 {
  margin: 0 0 1.5rem 0;
  color: var(--gray-800);
}

.tab-selector {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  background: white;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--gray-600);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.tab-btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 2rem;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--primary);
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
  margin-top: 0.25rem;
}

.section-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-card h3,
.section-card h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--gray-700);
}

.activity-grid,
.averages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius);
}

.activity-label {
  font-size: 0.875rem;
  color: var(--gray-600);
}

.activity-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--primary);
}

.avg-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius);
}

.avg-icon {
  font-size: 1.5rem;
}

.avg-content {
  display: flex;
  flex-direction: column;
}

.avg-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--gray-800);
}

.avg-label {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.efficiency-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.efficiency-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.efficiency-label {
  font-size: 0.875rem;
  color: var(--gray-600);
}

.progress-bar {
  height: 8px;
  background: var(--gray-200);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.3s;
}

.progress-fill.success {
  background: var(--success);
}

.efficiency-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-700);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.project-header h3 {
  margin: 0;
  color: var(--gray-800);
}

.time-spent {
  font-size: 0.875rem;
  color: var(--gray-500);
}

.completion-bar {
  height: 40px;
  background: var(--gray-200);
  border-radius: var(--radius);
  overflow: hidden;
  position: relative;
  margin-bottom: 1rem;
}

.completion-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), #60a5fa);
  transition: width 0.3s;
}

.completion-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.stages-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.75rem;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: var(--gray-50);
  border-radius: var(--radius);
  font-size: 0.875rem;
}

.stage-item.completed {
  background: #dcfce7;
}

.stage-icon {
  flex-shrink: 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
}

.detail-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--gray-800);
}

.detail-value.highlight {
  color: var(--primary);
}

.detail-value.success {
  color: var(--success);
}

.detail-value.pending {
  color: var(--gray-400);
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.timeline-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--primary);
  margin-top: 4px;
  flex-shrink: 0;
}

.timeline-dot.project_created {
  background: #10b981;
}

.timeline-dot.context_uploaded {
  background: #3b82f6;
}

.timeline-dot.features_extracted {
  background: #8b5cf6;
}

.timeline-dot.prd_generated {
  background: #f59e0b;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.timeline-desc {
  font-size: 0.875rem;
  color: var(--gray-700);
}

.timeline-time {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.loading-state {
  text-align: center;
  padding: 3rem;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .project-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>
