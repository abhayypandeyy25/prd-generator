<template>
  <div class="prd-tab">
    <!-- Warning Banners -->
    <div v-if="showWarnings && !isEditing" class="warnings-container">
      <!-- Critical: Very few confirmations -->
      <div v-if="confirmationPercentage < 20" class="warning-banner critical">
        <div class="warning-icon">⚠️</div>
        <div class="warning-content">
          <strong>Critical: Very Limited Data</strong>
          <p>Only {{ store.stats.confirmed }} of {{ store.stats.total_questions }} questions confirmed ({{ confirmationPercentage }}%).
             Your PRD will be significantly incomplete and may not be useful.</p>
        </div>
        <button class="btn btn-sm btn-warning" @click="goToQuestions">Review Questions</button>
      </div>

      <!-- Warning: Low confirmations -->
      <div v-else-if="confirmationPercentage < 50" class="warning-banner warning">
        <div class="warning-icon">⚡</div>
        <div class="warning-content">
          <strong>Limited Responses Available</strong>
          <p>Only {{ confirmationPercentage }}% of questions confirmed. The PRD you generate may have gaps.
             Consider confirming more responses for a comprehensive document.</p>
        </div>
        <button class="btn btn-sm btn-secondary" @click="goToQuestions">Confirm More</button>
      </div>

      <!-- Info: Could be better -->
      <div v-else-if="confirmationPercentage < 80" class="warning-banner info">
        <div class="warning-icon">💡</div>
        <div class="warning-content">
          <strong>Good Progress!</strong>
          <p>{{ confirmationPercentage }}% confirmed. You can generate now, or confirm more for better results.</p>
        </div>
      </div>

      <!-- No context files -->
      <div v-if="store.contextFiles.length === 0" class="warning-banner critical">
        <div class="warning-icon">📁</div>
        <div class="warning-content">
          <strong>No Context Files</strong>
          <p>You haven't uploaded any context documents. AI responses may be generic without context.</p>
        </div>
        <button class="btn btn-sm btn-warning" @click="goToContext">Upload Context</button>
      </div>

      <!-- No features selected -->
      <div v-if="store.activeFeatureCount === 0 && store.features.length > 0" class="warning-banner warning">
        <div class="warning-icon">✨</div>
        <div class="warning-content">
          <strong>No Features Selected</strong>
          <p>All features are in parking lot. Select features to include in your PRD.</p>
        </div>
        <button class="btn btn-sm btn-secondary" @click="goToFeatures">Select Features</button>
      </div>
    </div>

    <!-- Actions Bar -->
    <div v-if="!isEditing" class="card" style="margin-bottom: 1.5rem;">
      <div class="card-body">
        <div class="prd-actions">
          <div class="stats">
            <span :class="{ 'stat-warning': confirmationPercentage < 50 }">
              <strong>{{ store.stats.confirmed }}</strong> / {{ store.stats.total_questions }} questions confirmed
            </span>
            <span style="color: var(--gray-400);">|</span>
            <span :class="getCompletionClass">
              <strong>{{ confirmationPercentage }}%</strong> complete
            </span>
            <span v-if="store.activeFeatureCount > 0" style="color: var(--gray-400);">|</span>
            <span v-if="store.activeFeatureCount > 0">
              <strong>{{ store.activeFeatureCount }}</strong> features selected
            </span>
          </div>

          <div class="export-actions">
            <button
              class="btn btn-primary"
              @click="generatePRD"
              :disabled="isGenerating || store.stats.confirmed < 5"
              :title="store.stats.confirmed < 5 ? 'Confirm at least 5 questions to generate' : ''"
            >
              {{ store.prd ? '🔄 Regenerate PRD' : '✨ Generate PRD' }}
            </button>

            <template v-if="store.prd">
              <button class="btn btn-secondary" @click="enterEditMode">
                ✏️ Edit PRD
              </button>
              <button class="btn btn-secondary" @click="showStakeholderView = !showStakeholderView">
                {{ showStakeholderView ? '📄 Full PRD' : '👥 Stakeholder Views' }}
              </button>
              <button class="btn btn-secondary" @click="showFeedbackPanel = !showFeedbackPanel">
                {{ showFeedbackPanel ? '📄 Hide Feedback' : '💬 Feedback' }}
              </button>
              <button class="btn btn-secondary" @click="showShareModal = true">
                🔗 Share
              </button>
              <button class="btn btn-secondary" @click="exportPRD('md')">
                📄 Export Markdown
              </button>
              <button class="btn btn-secondary" @click="exportPRD('docx')">
                📘 Export Word
              </button>
              <button class="btn btn-secondary" @click="copyToClipboard">
                📋 Copy
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Mode Header -->
    <div v-if="isEditing" class="edit-mode-header">
      <button class="btn btn-secondary" @click="exitEditMode">
        ← Back to Preview
      </button>
      <h2>Editing PRD</h2>
      <div class="edit-mode-spacer"></div>
    </div>

    <!-- PRD Content / Editor -->
    <div class="prd-preview card" :class="{ editing: isEditing }">
      <!-- Edit Mode -->
      <PRDEditor
        v-if="isEditing"
        :initial-content="store.prd"
        @save="onEditorSave"
        @close="exitEditMode"
      />

      <!-- View Mode -->
      <template v-else>
        <div v-if="!store.prd && !isGenerating" class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>No PRD Generated Yet</h3>
          <p v-if="store.stats.confirmed < 5">
            You need to confirm at least 5 questions before generating a PRD.
            <br>Currently confirmed: <strong>{{ store.stats.confirmed }}</strong>
          </p>
          <p v-else>
            You have {{ store.stats.confirmed }} confirmed responses. Click "Generate PRD" to create your document.
          </p>

          <div class="empty-actions">
            <button
              v-if="store.stats.confirmed < 5"
              class="btn btn-primary"
              @click="store.setActiveTab('questions')"
            >
              ← Confirm More Questions
            </button>
            <button
              v-else
              class="btn btn-primary"
              @click="generatePRD"
              :disabled="isGenerating"
            >
              ✨ Generate PRD Now
            </button>
          </div>
        </div>

        <div v-else-if="isGenerating" class="loading">
          <div class="spinner"></div>
          <p style="margin-top: 1rem;">Generating your PRD with AI...</p>
          <p style="color: var(--gray-400); font-size: 0.875rem;">This may take a minute</p>
        </div>

        <!-- Stakeholder View -->
        <StakeholderView v-else-if="showStakeholderView" />

        <div v-else class="prd-content" v-html="renderedPRD"></div>
      </template>
    </div>

    <!-- Share Modal -->
    <ShareModal
      v-if="showShareModal && store.currentProject"
      :project-id="store.currentProject.id"
      @close="showShareModal = false"
    />

    <!-- Feedback Panel -->
    <FeedbackPanel
      v-if="showFeedbackPanel && store.prd"
      @close="showFeedbackPanel = false"
      @improved="showFeedbackPanel = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { useProjectStore } from '../stores/projectStore'
import PRDEditor from './PRDEditor.vue'
import ShareModal from './ShareModal.vue'
import StakeholderView from './StakeholderView.vue'
import FeedbackPanel from './FeedbackPanel.vue'

const store = useProjectStore()
const isGenerating = ref(false)
const isEditing = ref(false)
const showShareModal = ref(false)
const showStakeholderView = ref(false)
const showFeedbackPanel = ref(false)

// Configure marked for safe rendering
marked.setOptions({
  gfm: true,
  breaks: true
})

const confirmationPercentage = computed(() => {
  if (!store.stats.total_questions) return 0
  return Math.round((store.stats.confirmed / store.stats.total_questions) * 100)
})

const showWarnings = computed(() => {
  return confirmationPercentage.value < 80 ||
         store.contextFiles.length === 0 ||
         (store.activeFeatureCount === 0 && store.features.length > 0)
})

const getCompletionClass = computed(() => {
  if (confirmationPercentage.value >= 80) return 'stat-success'
  if (confirmationPercentage.value >= 50) return 'stat-warning'
  return 'stat-danger'
})

const renderedPRD = computed(() => {
  if (!store.prd) return ''
  return marked(store.prd)
})

onMounted(async () => {
  // Try to load existing PRD
  await store.fetchPRD()
})

const generatePRD = async () => {
  isGenerating.value = true
  try {
    await store.generatePRDWithoutLoading()
  } catch (error) {
    console.error('Failed to generate PRD:', error)
  } finally {
    isGenerating.value = false
  }
}

const exportPRD = async (format) => {
  await store.exportPRD(format)
}

const copyToClipboard = async () => {
  if (!store.prd) return

  try {
    await navigator.clipboard.writeText(store.prd)
    store.showToast('PRD copied to clipboard', 'success')
  } catch (error) {
    store.showToast('Failed to copy', 'error')
  }
}

const enterEditMode = () => {
  isEditing.value = true
}

const exitEditMode = () => {
  isEditing.value = false
}

const onEditorSave = (content) => {
  // PRD is saved via store, content already updated
  store.showToast('PRD saved successfully', 'success')
}

const goToQuestions = () => {
  store.setActiveTab('questions')
}

const goToContext = () => {
  store.setActiveTab('context')
}

const goToFeatures = () => {
  store.setActiveTab('features')
}
</script>

<style scoped>
.warnings-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.warning-banner {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-lg);
  background: white;
  border-left: 4px solid;
}

.warning-banner.critical {
  border-left-color: var(--error);
  background: #fef2f2;
}

.warning-banner.warning {
  border-left-color: var(--warning);
  background: #fffbeb;
}

.warning-banner.info {
  border-left-color: var(--primary);
  background: var(--primary-light);
}

.warning-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.warning-content {
  flex: 1;
}

.warning-content strong {
  display: block;
  margin-bottom: 0.25rem;
  color: var(--gray-800);
}

.warning-content p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--gray-600);
  line-height: 1.4;
}

.btn-warning {
  background: var(--error);
  color: white;
}

.btn-warning:hover {
  background: #dc2626;
}

.prd-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.stats {
  display: flex;
  gap: 1rem;
  color: var(--gray-600);
  flex-wrap: wrap;
}

.stat-success {
  color: var(--success);
}

.stat-warning {
  color: #d97706;
}

.stat-danger {
  color: var(--error);
}

.export-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin-bottom: 0.5rem;
  color: var(--gray-700);
}

.empty-state p {
  color: var(--gray-500);
  margin-bottom: 2rem;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.empty-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.prd-content {
  padding: 2rem;
}

/* Markdown content styling */
.prd-content :deep(h1) {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: var(--gray-900);
  border-bottom: 3px solid var(--primary);
  padding-bottom: 0.5rem;
}

.prd-content :deep(h2) {
  font-size: 1.5rem;
  margin-top: 2.5rem;
  margin-bottom: 1rem;
  color: var(--gray-800);
  border-bottom: 2px solid var(--gray-200);
  padding-bottom: 0.5rem;
}

.prd-content :deep(h3) {
  font-size: 1.25rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: var(--gray-700);
}

.prd-content :deep(h4) {
  font-size: 1.125rem;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
  color: var(--gray-700);
}

.prd-content :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.7;
}

.prd-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-size: 0.9375rem;
}

.prd-content :deep(th),
.prd-content :deep(td) {
  padding: 0.75rem 1rem;
  border: 1px solid var(--gray-200);
  text-align: left;
}

.prd-content :deep(th) {
  background: var(--gray-50);
  font-weight: 600;
  color: var(--gray-700);
}

.prd-content :deep(tr:hover) {
  background: var(--gray-50);
}

.prd-content :deep(blockquote) {
  border-left: 4px solid var(--primary);
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  background: var(--primary-light);
  color: var(--gray-700);
  border-radius: 0 var(--radius) var(--radius) 0;
}

.prd-content :deep(blockquote p) {
  margin: 0;
}

.prd-content :deep(code) {
  background: var(--gray-100);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.875em;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
}

.prd-content :deep(pre) {
  background: var(--gray-800);
  color: var(--gray-100);
  padding: 1.25rem;
  border-radius: var(--radius);
  overflow-x: auto;
  margin: 1.5rem 0;
}

.prd-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.prd-content :deep(ul),
.prd-content :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.prd-content :deep(li) {
  margin-bottom: 0.5rem;
  line-height: 1.6;
}

.prd-content :deep(hr) {
  border: none;
  border-top: 2px solid var(--gray-200);
  margin: 2rem 0;
}

.prd-content :deep(strong) {
  font-weight: 600;
  color: var(--gray-900);
}

.prd-content :deep(a) {
  color: var(--primary);
  text-decoration: none;
}

.prd-content :deep(a:hover) {
  text-decoration: underline;
}

/* Checkbox styling in markdown */
.prd-content :deep(input[type="checkbox"]) {
  margin-right: 0.5rem;
}

/* Edit Mode */
.edit-mode-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.edit-mode-header h2 {
  flex: 1;
  margin: 0;
  font-size: 1.25rem;
  color: var(--gray-800);
}

.edit-mode-spacer {
  width: 120px;
}

.prd-preview.editing {
  height: calc(100vh - 200px);
  min-height: 500px;
  padding: 0;
}

.prd-preview.editing .prd-content {
  padding: 0;
}

@media (max-width: 768px) {
  .prd-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .export-actions {
    flex-direction: column;
  }

  .prd-content {
    padding: 1rem;
  }

  .warning-banner {
    flex-direction: column;
    text-align: center;
  }
}
</style>
