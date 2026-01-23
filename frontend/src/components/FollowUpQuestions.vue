<template>
  <div v-if="followUps.length > 0 || relatedQuestions.length > 0" class="follow-up-questions">
    <!-- Follow-up Questions -->
    <div v-if="followUps.length > 0" class="follow-up-section">
      <div class="section-header">
        <span class="section-icon">💡</span>
        <h4>Follow-up Questions</h4>
        <span class="section-badge">{{ followUps.length }}</span>
      </div>

      <div class="follow-up-list">
        <div
          v-for="fu in followUps"
          :key="fu.id"
          class="follow-up-item"
          :class="{ answered: answeredFollowUps[fu.id] }"
        >
          <div class="fu-header">
            <span class="fu-type-badge" :class="fu.type">
              {{ fu.type === 'ai_generated' ? '🤖 AI' : '📋 Auto' }}
            </span>
            <span class="fu-question">{{ fu.question }}</span>
          </div>

          <p v-if="fu.hint" class="fu-hint">{{ fu.hint }}</p>

          <div v-if="!answeredFollowUps[fu.id]" class="fu-input">
            <textarea
              v-model="followUpResponses[fu.id]"
              :placeholder="fu.hint || 'Enter your response...'"
              rows="2"
            ></textarea>
            <button
              class="btn btn-sm btn-primary"
              @click="saveFollowUp(fu)"
              :disabled="!followUpResponses[fu.id]?.trim()"
            >
              Save
            </button>
          </div>

          <div v-else class="fu-answered">
            <span class="answered-icon">✓</span>
            <span class="answered-text">{{ answeredFollowUps[fu.id] }}</span>
            <button class="btn btn-sm btn-secondary" @click="editFollowUp(fu.id)">
              Edit
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Related Questions -->
    <div v-if="relatedQuestions.length > 0" class="related-section">
      <div class="section-header">
        <span class="section-icon">🔗</span>
        <h4>Related Questions</h4>
      </div>

      <div class="related-list">
        <div
          v-for="rq in relatedQuestions"
          :key="rq.id"
          class="related-item"
          @click="$emit('navigate-to-question', rq.id)"
        >
          <span class="related-id">{{ rq.id }}</span>
          <span class="related-question">{{ rq.question }}</span>
          <span class="related-arrow">→</span>
        </div>
      </div>
    </div>

    <!-- Skipped Questions Notice -->
    <div v-if="skippedQuestions.length > 0" class="skipped-section">
      <div class="section-header">
        <span class="section-icon">⏭️</span>
        <h4>Questions Skipped</h4>
      </div>
      <p class="skipped-notice">
        Based on your response, the following questions have been skipped:
        <strong>{{ skippedQuestions.join(', ') }}</strong>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { questionsApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'

const props = defineProps({
  questionId: { type: String, required: true },
  questionText: { type: String, default: '' },
  responseText: { type: String, default: '' },
  followUps: { type: Array, default: () => [] },
  aiFollowUps: { type: Array, default: () => [] },
  relatedQuestions: { type: Array, default: () => [] },
  skippedQuestions: { type: Array, default: () => [] }
})

const emit = defineEmits(['navigate-to-question', 'follow-up-saved'])

const store = useProjectStore()
const followUpResponses = ref({})
const answeredFollowUps = ref({})

// Combine rule-based and AI follow-ups
const allFollowUps = () => {
  return [...props.followUps, ...props.aiFollowUps]
}

const saveFollowUp = async (followUp) => {
  const response = followUpResponses.value[followUp.id]?.trim()
  if (!response || !store.currentProject?.id) return

  try {
    await questionsApi.saveFollowUp(store.currentProject.id, {
      follow_up_id: followUp.id,
      parent_question_id: props.questionId,
      question: followUp.question,
      response: response
    })

    answeredFollowUps.value[followUp.id] = response
    emit('follow-up-saved', { followUpId: followUp.id, response })
    store.showToast('Follow-up saved', 'success')
  } catch (error) {
    console.error('Failed to save follow-up:', error)
    store.showToast('Failed to save follow-up', 'error')
  }
}

const editFollowUp = (followUpId) => {
  followUpResponses.value[followUpId] = answeredFollowUps.value[followUpId]
  delete answeredFollowUps.value[followUpId]
}

// Watch for response changes to reset follow-up state
watch(() => props.responseText, () => {
  followUpResponses.value = {}
  answeredFollowUps.value = {}
})
</script>

<style scoped>
.follow-up-questions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px dashed var(--gray-200);
}

.follow-up-section,
.related-section,
.skipped-section {
  margin-bottom: 1.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.section-icon {
  font-size: 1rem;
}

.section-header h4 {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-700);
}

.section-badge {
  background: var(--primary);
  color: white;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
}

.follow-up-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.follow-up-item {
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius);
  border-left: 3px solid var(--primary);
}

.follow-up-item.answered {
  border-left-color: var(--success);
  background: #f0fdf4;
}

.fu-header {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.fu-type-badge {
  flex-shrink: 0;
  font-size: 0.625rem;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: 600;
}

.fu-type-badge.follow_up {
  background: #dbeafe;
  color: #1e40af;
}

.fu-type-badge.ai_generated {
  background: #f3e8ff;
  color: #7c3aed;
}

.fu-question {
  font-weight: 500;
  color: var(--gray-800);
  font-size: 0.875rem;
}

.fu-hint {
  margin: 0 0 0.75rem 0;
  font-size: 0.75rem;
  color: var(--gray-500);
  font-style: italic;
}

.fu-input {
  display: flex;
  gap: 0.5rem;
}

.fu-input textarea {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 0.875rem;
  resize: vertical;
  min-height: 60px;
}

.fu-input textarea:focus {
  outline: none;
  border-color: var(--primary);
}

.fu-answered {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  background: white;
  border-radius: var(--radius);
}

.answered-icon {
  color: var(--success);
  font-weight: bold;
}

.answered-text {
  flex: 1;
  font-size: 0.875rem;
  color: var(--gray-700);
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.related-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--gray-50);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.2s;
}

.related-item:hover {
  background: var(--gray-100);
}

.related-id {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-light);
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.related-question {
  flex: 1;
  font-size: 0.875rem;
  color: var(--gray-700);
}

.related-arrow {
  color: var(--gray-400);
}

.skipped-notice {
  margin: 0;
  padding: 0.75rem;
  background: #fef3c7;
  border-radius: var(--radius);
  font-size: 0.875rem;
  color: var(--gray-700);
}
</style>
