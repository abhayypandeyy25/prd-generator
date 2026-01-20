<template>
  <div class="prd-tab">
    <!-- Actions Bar -->
    <div class="card" style="margin-bottom: 1.5rem;">
      <div class="card-body">
        <div class="prd-actions">
          <div class="stats">
            <span>
              <strong>{{ store.stats.confirmed }}</strong> questions confirmed
            </span>
            <span style="color: var(--gray-400);">|</span>
            <span>
              <strong>{{ store.completionPercentage }}%</strong> complete
            </span>
          </div>

          <div class="export-actions">
            <button
              class="btn btn-primary"
              @click="generatePRD"
              :disabled="store.loading || store.stats.confirmed < 10"
            >
              {{ store.prd ? '🔄 Regenerate PRD' : '✨ Generate PRD' }}
            </button>

            <template v-if="store.prd">
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

    <!-- PRD Content -->
    <div class="prd-preview card">
      <div v-if="!store.prd && !store.loading" class="empty-state">
        <div class="empty-icon">📋</div>
        <h3>No PRD Generated Yet</h3>
        <p>
          Answer and confirm at least 10 questions, then click "Generate PRD" to create your document.
        </p>
        <button
          class="btn btn-primary"
          @click="store.setActiveTab('questions')"
        >
          ← Back to Questions
        </button>
      </div>

      <div v-else-if="store.loading" class="loading">
        <div class="spinner"></div>
        <p style="margin-top: 1rem;">Generating your PRD with AI...</p>
        <p style="color: var(--gray-400); font-size: 0.875rem;">This may take a minute</p>
      </div>

      <div v-else class="prd-content" v-html="renderedPRD"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()

// Configure marked for safe rendering
marked.setOptions({
  gfm: true,
  breaks: true
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
  try {
    await store.generatePRD()
  } catch (error) {
    console.error('Failed to generate PRD:', error)
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
</script>

<style scoped>
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
}
</style>
