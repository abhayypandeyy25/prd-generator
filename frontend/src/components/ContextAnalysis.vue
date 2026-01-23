<template>
  <div class="context-analysis">
    <!-- Analysis Header -->
    <div class="analysis-header">
      <h3>Context Quality Analysis</h3>
      <div class="header-actions">
        <button
          class="btn btn-secondary btn-sm"
          @click="refreshAnalysis"
          :disabled="loading"
        >
          {{ loading ? 'Analyzing...' : '🔄 Refresh' }}
        </button>
        <button
          class="btn btn-primary btn-sm"
          @click="runDeepAnalysis"
          :disabled="deepLoading || !hasFiles"
          :title="!hasFiles ? 'Upload files first' : 'Run AI-powered deep analysis'"
        >
          {{ deepLoading ? 'Running AI Analysis...' : '🤖 Deep Analysis' }}
        </button>
      </div>
    </div>

    <!-- Quality Score Card -->
    <div v-if="analysis" class="score-card">
      <div class="score-circle" :class="scoreClass">
        <span class="score-value">{{ analysis.quality_score }}</span>
        <span class="score-label">/ 100</span>
      </div>
      <div class="score-details">
        <h4>{{ analysis.summary }}</h4>
        <div class="metrics-row">
          <div class="metric">
            <span class="metric-value">{{ analysis.metrics?.file_count || 0 }}</span>
            <span class="metric-label">Files</span>
          </div>
          <div class="metric">
            <span class="metric-value">{{ formatNumber(analysis.metrics?.total_characters || 0) }}</span>
            <span class="metric-label">Characters</span>
          </div>
          <div class="metric">
            <span class="metric-value">{{ analysis.metrics?.unique_file_types || 0 }}</span>
            <span class="metric-label">File Types</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Coverage Grid -->
    <div v-if="analysis?.coverage" class="coverage-section">
      <h4>Coverage Analysis</h4>
      <div class="coverage-grid">
        <div
          v-for="(item, key) in analysis.coverage"
          :key="key"
          class="coverage-item"
          :class="{ covered: item.found, missing: !item.found }"
        >
          <span class="coverage-icon">{{ item.found ? '✅' : '❌' }}</span>
          <span class="coverage-label">{{ item.description }}</span>
          <span v-if="item.found" class="coverage-count">{{ item.match_count }} mentions</span>
        </div>
      </div>
    </div>

    <!-- Suggestions -->
    <div v-if="analysis?.suggestions?.length" class="suggestions-section">
      <h4>💡 Suggestions</h4>
      <ul class="suggestions-list">
        <li v-for="(suggestion, idx) in analysis.suggestions" :key="idx">
          {{ suggestion }}
        </li>
      </ul>
    </div>

    <!-- Entities Found -->
    <div v-if="hasEntities" class="entities-section">
      <h4>🔍 Extracted Information</h4>
      <div class="entities-grid">
        <div v-if="analysis.entities?.dates?.length" class="entity-group">
          <span class="entity-label">📅 Dates</span>
          <div class="entity-tags">
            <span v-for="date in analysis.entities.dates.slice(0, 5)" :key="date" class="tag">{{ date }}</span>
          </div>
        </div>
        <div v-if="analysis.entities?.percentages?.length" class="entity-group">
          <span class="entity-label">📊 Percentages</span>
          <div class="entity-tags">
            <span v-for="pct in analysis.entities.percentages.slice(0, 5)" :key="pct" class="tag">{{ pct }}</span>
          </div>
        </div>
        <div v-if="analysis.entities?.monetary?.length" class="entity-group">
          <span class="entity-label">💰 Monetary</span>
          <div class="entity-tags">
            <span v-for="money in analysis.entities.monetary.slice(0, 5)" :key="money" class="tag">{{ money }}</span>
          </div>
        </div>
        <div v-if="analysis.entities?.technical_terms?.length" class="entity-group">
          <span class="entity-label">⚙️ Technical Terms</span>
          <div class="entity-tags">
            <span v-for="term in analysis.entities.technical_terms.slice(0, 8)" :key="term" class="tag tech">{{ term }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Conflicts Warning -->
    <div v-if="analysis?.conflicts?.length" class="conflicts-section">
      <h4>⚠️ Potential Conflicts</h4>
      <div class="conflicts-list">
        <div v-for="(conflict, idx) in analysis.conflicts" :key="idx" class="conflict-item">
          <span class="conflict-icon">⚡</span>
          <span class="conflict-message">{{ conflict.message }}</span>
        </div>
      </div>
    </div>

    <!-- AI Deep Analysis Results -->
    <div v-if="analysis?.ai_analysis" class="ai-analysis-section">
      <h4>🤖 AI Deep Analysis</h4>

      <div v-if="analysis.ai_analysis.key_themes?.length" class="ai-group">
        <h5>Key Themes</h5>
        <div class="ai-tags">
          <span v-for="theme in analysis.ai_analysis.key_themes" :key="theme" class="tag theme">{{ theme }}</span>
        </div>
      </div>

      <div v-if="analysis.ai_analysis.stakeholders_mentioned?.length" class="ai-group">
        <h5>Stakeholders Mentioned</h5>
        <div class="ai-tags">
          <span v-for="stakeholder in analysis.ai_analysis.stakeholders_mentioned" :key="stakeholder" class="tag stakeholder">{{ stakeholder }}</span>
        </div>
      </div>

      <div v-if="analysis.ai_analysis.potential_risks?.length" class="ai-group">
        <h5>Potential Risks</h5>
        <ul class="ai-list risks">
          <li v-for="risk in analysis.ai_analysis.potential_risks" :key="risk">{{ risk }}</li>
        </ul>
      </div>

      <div v-if="analysis.ai_analysis.missing_info?.length" class="ai-group">
        <h5>Missing Information</h5>
        <ul class="ai-list missing">
          <li v-for="info in analysis.ai_analysis.missing_info" :key="info">{{ info }}</li>
        </ul>
      </div>

      <div v-if="analysis.ai_analysis.recommendations?.length" class="ai-group">
        <h5>Recommendations</h5>
        <ul class="ai-list recommendations">
          <li v-for="rec in analysis.ai_analysis.recommendations" :key="rec">{{ rec }}</li>
        </ul>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !analysis" class="empty-state">
      <div class="empty-icon">📊</div>
      <h4>No Analysis Available</h4>
      <p>Upload context files and click "Refresh" to analyze your context quality.</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !analysis" class="loading-state">
      <div class="spinner"></div>
      <p>Analyzing context...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { contextApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()

const analysis = ref(null)
const loading = ref(false)
const deepLoading = ref(false)

const hasFiles = computed(() => store.contextFiles.length > 0)

const hasEntities = computed(() => {
  if (!analysis.value?.entities) return false
  const e = analysis.value.entities
  return (e.dates?.length || e.percentages?.length || e.monetary?.length || e.technical_terms?.length)
})

const scoreClass = computed(() => {
  if (!analysis.value) return ''
  const score = analysis.value.quality_score
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'moderate'
  return 'low'
})

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

const refreshAnalysis = async () => {
  if (!store.currentProject?.id) return

  loading.value = true
  try {
    const response = await contextApi.analyze(store.currentProject.id)
    analysis.value = response.data
  } catch (error) {
    console.error('Analysis failed:', error)
    store.showToast('Failed to analyze context', 'error')
  } finally {
    loading.value = false
  }
}

const runDeepAnalysis = async () => {
  if (!store.currentProject?.id) return

  deepLoading.value = true
  try {
    const response = await contextApi.deepAnalyze(store.currentProject.id)
    analysis.value = response.data
    store.showToast('Deep analysis complete', 'success')
  } catch (error) {
    console.error('Deep analysis failed:', error)
    store.showToast('Deep analysis failed', 'error')
  } finally {
    deepLoading.value = false
  }
}

// Auto-refresh when context files change
watch(() => store.contextFiles.length, () => {
  if (store.currentProject?.id) {
    refreshAnalysis()
  }
})

onMounted(() => {
  if (store.currentProject?.id && store.contextFiles.length > 0) {
    refreshAnalysis()
  }
})

defineExpose({ refreshAnalysis })
</script>

<style scoped>
.context-analysis {
  background: white;
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  margin-top: 1.5rem;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.analysis-header h3 {
  margin: 0;
  color: var(--gray-800);
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.score-card {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.5rem;
  background: var(--gray-50);
  border-radius: var(--radius-lg);
  margin-bottom: 1.5rem;
}

.score-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border: 4px solid;
  flex-shrink: 0;
}

.score-circle.excellent {
  border-color: var(--success);
  color: var(--success);
}

.score-circle.good {
  border-color: #22c55e;
  color: #22c55e;
}

.score-circle.moderate {
  border-color: var(--warning);
  color: var(--warning);
}

.score-circle.low {
  border-color: var(--error);
  color: var(--error);
}

.score-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.score-details {
  flex: 1;
}

.score-details h4 {
  margin: 0 0 1rem 0;
  color: var(--gray-700);
}

.metrics-row {
  display: flex;
  gap: 2rem;
}

.metric {
  display: flex;
  flex-direction: column;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--gray-800);
}

.metric-label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
}

.coverage-section,
.suggestions-section,
.entities-section,
.conflicts-section,
.ai-analysis-section {
  margin-bottom: 1.5rem;
}

.coverage-section h4,
.suggestions-section h4,
.entities-section h4,
.conflicts-section h4,
.ai-analysis-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--gray-700);
}

.coverage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}

.coverage-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: var(--radius);
  background: var(--gray-50);
  font-size: 0.875rem;
}

.coverage-item.covered {
  background: #dcfce7;
}

.coverage-item.missing {
  background: #fee2e2;
}

.coverage-icon {
  flex-shrink: 0;
}

.coverage-label {
  flex: 1;
  color: var(--gray-700);
}

.coverage-count {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.suggestions-list {
  margin: 0;
  padding-left: 1.5rem;
}

.suggestions-list li {
  margin-bottom: 0.5rem;
  color: var(--gray-600);
}

.entities-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.entity-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.entity-label {
  font-weight: 500;
  color: var(--gray-700);
  font-size: 0.875rem;
}

.entity-tags,
.ai-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  background: var(--gray-100);
  color: var(--gray-700);
}

.tag.tech {
  background: #dbeafe;
  color: #1e40af;
}

.tag.theme {
  background: #f3e8ff;
  color: #7c3aed;
}

.tag.stakeholder {
  background: #fef3c7;
  color: #92400e;
}

.conflicts-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.conflict-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #fef3c7;
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: var(--gray-700);
}

.ai-analysis-section {
  background: linear-gradient(135deg, #f0f9ff 0%, #f5f3ff 100%);
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  margin-top: 1.5rem;
}

.ai-group {
  margin-bottom: 1.25rem;
}

.ai-group:last-child {
  margin-bottom: 0;
}

.ai-group h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: var(--gray-600);
}

.ai-list {
  margin: 0;
  padding-left: 1.5rem;
}

.ai-list li {
  margin-bottom: 0.375rem;
  font-size: 0.875rem;
  color: var(--gray-700);
}

.ai-list.risks li {
  color: #b91c1c;
}

.ai-list.missing li {
  color: #d97706;
}

.ai-list.recommendations li {
  color: #047857;
}

.empty-state,
.loading-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--gray-500);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h4 {
  margin: 0 0 0.5rem 0;
  color: var(--gray-700);
}

.empty-state p {
  margin: 0;
}

@media (max-width: 768px) {
  .score-card {
    flex-direction: column;
    text-align: center;
  }

  .metrics-row {
    justify-content: center;
  }

  .coverage-grid {
    grid-template-columns: 1fr;
  }
}
</style>
