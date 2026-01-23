<template>
  <div class="questions-tab">
    <!-- AI Processing Overlay -->
    <div v-if="isPrefilling" class="ai-processing-overlay">
      <div class="ai-processing-card">
        <div class="ai-spinner"></div>
        <h3 class="ai-title">AI is analyzing your context...</h3>
        <div class="ai-progress-info">
          <div class="ai-counter">
            <span class="counter-current">{{ prefillProgress.processed }}</span>
            <span class="counter-separator">/</span>
            <span class="counter-total">{{ prefillProgress.total }}</span>
          </div>
          <p class="ai-status">questions processed</p>
        </div>
        <div class="ai-progress-bar">
          <div
            class="ai-progress-fill"
            :style="{ width: prefillProgressPercent + '%' }"
          ></div>
        </div>
        <p class="ai-hint">Using context + {{ store.activeFeatureCount }} selected features</p>
      </div>
    </div>

    <!-- Progress & Actions Bar -->
    <div class="card" style="margin-bottom: 1.5rem;">
      <div class="card-body">
        <div class="progress-header">
          <div style="flex: 1;">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: store.completionPercentage + '%' }"></div>
            </div>
            <div class="progress-text">
              {{ store.stats.confirmed }} of {{ store.stats.total_questions }} questions confirmed
              ({{ store.completionPercentage }}% complete)
            </div>
          </div>
          <div class="action-buttons">
            <button
              class="btn btn-primary"
              @click="prefillWithAI"
              :disabled="store.contextFiles.length === 0 || store.loading || isPrefilling"
            >
              🤖 AI Prefill from Context
            </button>
            <button
              class="btn btn-success"
              @click="goToPRD"
              :disabled="store.stats.confirmed < 10"
            >
              Generate PRD →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Section Navigation -->
    <div class="section-nav">
      <button
        v-for="section in store.questions.sections"
        :key="section.id"
        class="section-btn"
        :class="{ active: activeSection === section.id }"
        @click="activeSection = section.id"
      >
        {{ section.id }}. {{ truncate(section.title.replace('Part ' + section.id + ': ', ''), 20) }}
      </button>
    </div>

    <!-- Filter -->
    <div class="filter-bar">
      <button
        class="filter-btn"
        :class="{ active: filter === 'all' }"
        @click="filter = 'all'"
      >
        All
      </button>
      <button
        class="filter-btn"
        :class="{ active: filter === 'confirmed' }"
        @click="filter = 'confirmed'"
      >
        ✓ Confirmed
      </button>
      <button
        class="filter-btn"
        :class="{ active: filter === 'needs-input' }"
        @click="filter = 'needs-input'"
      >
        ⚠ Needs Input
      </button>
    </div>

    <!-- Questions List -->
    <div class="questions-list">
      <template v-for="section in store.questions.sections" :key="section.id">
        <template v-if="activeSection === section.id">
          <div v-for="subsection in section.subsections" :key="subsection.id" class="subsection">
            <h3 class="subsection-title">{{ subsection.title }}</h3>

            <QuestionCard
              v-for="question in filteredQuestions(subsection.questions)"
              :key="question.id"
              :question="question"
              :response="store.getResponseByQuestionId(question.id)"
              @save="(response, confirmed) => saveResponse(question.id, response, confirmed)"
              @confirm="(confirmed) => confirmResponse(question.id, confirmed)"
              @navigate-to-question="navigateToQuestion"
            />

            <div
              v-if="filteredQuestions(subsection.questions).length === 0"
              style="text-align: center; padding: 2rem; color: var(--gray-400);"
            >
              No questions match the current filter
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import QuestionCard from './QuestionCard.vue'

const store = useProjectStore()

const activeSection = ref(store.questions.sections?.[0]?.id || '1')
const filter = ref('all')
const isPrefilling = ref(false)
const prefillProgress = ref({ processed: 0, total: 139 })
let progressInterval = null

const prefillProgressPercent = computed(() => {
  if (prefillProgress.value.total === 0) return 0
  return Math.round((prefillProgress.value.processed / prefillProgress.value.total) * 100)
})

const filteredQuestions = (questions) => {
  if (!questions) return []

  return questions.filter(q => {
    const response = store.getResponseByQuestionId(q.id)

    if (filter.value === 'confirmed') {
      return response?.confirmed
    }

    if (filter.value === 'needs-input') {
      return !response?.response || !response?.confirmed
    }

    return true
  })
}

const truncate = (text, length) => {
  return text.length > length ? text.substring(0, length) + '...' : text
}

const simulateProgress = () => {
  // Simulate progress animation while waiting for API
  const totalQuestions = store.stats.total_questions || 139
  prefillProgress.value = { processed: 0, total: totalQuestions }

  progressInterval = setInterval(() => {
    if (prefillProgress.value.processed < totalQuestions - 10) {
      // Increment by random amount to simulate batch processing
      const increment = Math.floor(Math.random() * 8) + 3
      prefillProgress.value.processed = Math.min(
        prefillProgress.value.processed + increment,
        totalQuestions - 10
      )
    }
  }, 800)
}

const stopProgress = (finalCount) => {
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
  // Set to final count
  prefillProgress.value.processed = finalCount || prefillProgress.value.total
}

const prefillWithAI = async () => {
  if (store.contextFiles.length === 0) {
    store.showToast('Please upload context files first', 'error')
    return
  }

  isPrefilling.value = true
  simulateProgress()

  try {
    const result = await store.prefillQuestions()
    const answeredCount = result?.responses?.length || 0
    stopProgress(answeredCount)

    // Brief pause to show final count
    await new Promise(resolve => setTimeout(resolve, 500))
  } catch (error) {
    console.error('Prefill failed:', error)
    stopProgress(0)
  } finally {
    isPrefilling.value = false
  }
}

onUnmounted(() => {
  if (progressInterval) {
    clearInterval(progressInterval)
  }
})

const saveResponse = async (questionId, response, confirmed) => {
  await store.saveResponse(questionId, response, confirmed)
}

const confirmResponse = async (questionId, confirmed) => {
  await store.confirmResponse(questionId, confirmed)
}

const goToPRD = () => {
  store.setActiveTab('prd')
}

const navigateToQuestion = (questionId) => {
  // Parse the question ID to find the section (e.g., "1.2.3" -> section "1")
  const sectionId = questionId.split('.')[0]
  if (sectionId) {
    activeSection.value = sectionId
    // Scroll to the question after a brief delay for DOM update
    setTimeout(() => {
      const questionElement = document.querySelector(`[data-question-id="${questionId}"]`)
      if (questionElement) {
        questionElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        questionElement.classList.add('highlight')
        setTimeout(() => questionElement.classList.remove('highlight'), 2000)
      }
    }, 100)
  }
}
</script>

<style scoped>
/* AI Processing Overlay */
.ai-processing-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.ai-processing-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 2.5rem 3rem;
  text-align: center;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}

.ai-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1.5rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.ai-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0 0 1.5rem 0;
}

.ai-progress-info {
  margin-bottom: 1rem;
}

.ai-counter {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
}

.counter-current {
  color: var(--primary);
  animation: pulse 0.5s ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.counter-separator {
  color: var(--gray-400);
  margin: 0 0.25rem;
}

.counter-total {
  color: var(--gray-500);
}

.ai-status {
  color: var(--gray-500);
  font-size: 0.9375rem;
  margin: 0.5rem 0 0 0;
}

.ai-progress-bar {
  height: 8px;
  background: var(--gray-200);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.ai-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), #60a5fa);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.ai-hint {
  color: var(--gray-400);
  font-size: 0.8125rem;
  margin: 0;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
}

.filter-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: var(--gray-600);
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  background: var(--gray-50);
}

.filter-btn.active {
  background: var(--primary-light);
  border-color: var(--primary);
  color: var(--primary);
}

.subsection {
  margin-bottom: 2rem;
}

.subsection-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid var(--gray-200);
}

/* Highlight animation for navigated questions */
:deep(.question-card.highlight) {
  animation: highlightPulse 2s ease-in-out;
}

@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  50% {
    box-shadow: 0 0 0 4px var(--primary), 0 4px 20px rgba(99, 102, 241, 0.3);
  }
}

@media (max-width: 768px) {
  .progress-header {
    flex-direction: column;
    align-items: stretch;
  }

  .action-buttons {
    flex-direction: column;
  }

  .section-nav {
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }

  .section-btn {
    white-space: nowrap;
  }
}
</style>
