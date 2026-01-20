<template>
  <div class="questions-tab">
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
              :disabled="store.contextFiles.length === 0 || store.loading"
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
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import QuestionCard from './QuestionCard.vue'

const store = useProjectStore()

const activeSection = ref(store.questions.sections?.[0]?.id || '1')
const filter = ref('all')

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

const prefillWithAI = async () => {
  if (store.contextFiles.length === 0) {
    store.showToast('Please upload context files first', 'error')
    return
  }

  try {
    await store.prefillQuestions()
  } catch (error) {
    console.error('Prefill failed:', error)
  }
}

const saveResponse = async (questionId, response, confirmed) => {
  await store.saveResponse(questionId, response, confirmed)
}

const confirmResponse = async (questionId, confirmed) => {
  await store.confirmResponse(questionId, confirmed)
}

const goToPRD = () => {
  store.setActiveTab('prd')
}
</script>

<style scoped>
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
