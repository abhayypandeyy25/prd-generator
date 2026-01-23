<template>
  <div
    class="question-card"
    :class="{
      confirmed: response?.confirmed,
      'needs-input': !response?.response && !response?.confirmed
    }"
    :data-question-id="question.id"
  >
    <div class="question-header">
      <span class="question-id">{{ question.id }}</span>
      <span class="question-text">
        {{ question.question }}
        <span v-if="question.required" style="color: var(--danger);">*</span>
      </span>
    </div>

    <div v-if="question.hint" class="question-hint">
      💡 {{ question.hint }}
    </div>

    <div class="question-input">
      <!-- Textarea for text/textarea type -->
      <template v-if="question.type === 'textarea' || question.type === 'text'">
        <textarea
          v-if="question.type === 'textarea'"
          v-model="localResponse"
          :placeholder="'Enter your response...'"
          @blur="saveOnBlur"
          rows="4"
        ></textarea>
        <input
          v-else
          type="text"
          v-model="localResponse"
          :placeholder="'Enter your response...'"
          @blur="saveOnBlur"
        >
      </template>

      <!-- Number input -->
      <template v-else-if="question.type === 'number'">
        <input
          type="number"
          v-model="localResponse"
          :min="question.min"
          :max="question.max"
          :placeholder="`Enter a number (${question.min}-${question.max})`"
          @blur="saveOnBlur"
        >
      </template>

      <!-- Single select (checkbox in original) -->
      <template v-else-if="question.type === 'checkbox'">
        <div class="options-list">
          <div
            v-for="option in question.options"
            :key="option"
            class="option-item"
            :class="{ selected: localResponse === option }"
            @click="selectOption(option)"
          >
            <input
              type="radio"
              :name="question.id"
              :checked="localResponse === option"
            >
            <span>{{ option }}</span>
          </div>
        </div>
      </template>

      <!-- Multi-select -->
      <template v-else-if="question.type === 'multiselect'">
        <div class="options-list">
          <div
            v-for="option in question.options"
            :key="option"
            class="option-item"
            :class="{ selected: selectedOptions.includes(option) }"
            @click="toggleOption(option)"
          >
            <input
              type="checkbox"
              :checked="selectedOptions.includes(option)"
            >
            <span>{{ option }}</span>
          </div>
        </div>
      </template>
    </div>

    <div class="question-actions">
      <div class="badges">
        <span v-if="response?.ai_suggested" class="ai-badge">
          🤖 AI Suggested
        </span>
        <span
          v-if="response?.confidence"
          :class="['confidence-badge', `confidence-${response.confidence}`]"
        >
          {{ response.confidence }} confidence
        </span>
      </div>

      <div class="action-buttons">
        <button
          v-if="!response?.confirmed && localResponse && localResponse.trim()"
          class="btn btn-secondary btn-sm"
          @click="getSmartSuggestion"
          :disabled="suggestLoading"
          title="Get AI suggestion based on context"
        >
          {{ suggestLoading ? '...' : '💡 Suggest' }}
        </button>
        <button
          v-if="response?.confirmed"
          class="btn btn-secondary"
          @click="unconfirm"
        >
          ↩ Edit
        </button>
        <button
          v-else
          class="btn btn-success"
          @click="confirm"
          :disabled="!localResponse || localResponse.trim() === ''"
        >
          ✓ Confirm
        </button>
      </div>
    </div>

    <!-- Follow-up Questions -->
    <FollowUpQuestions
      v-if="response?.confirmed && followUpData"
      :question-id="question.id"
      :question-text="question.question"
      :response-text="localResponse"
      :follow-ups="followUpData.follow_ups || []"
      :ai-follow-ups="followUpData.ai_follow_ups || []"
      :related-questions="followUpData.related_questions || []"
      :skipped-questions="followUpData.skip_questions || []"
      @navigate-to-question="$emit('navigate-to-question', $event)"
      @follow-up-saved="onFollowUpSaved"
    />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { questionsApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'
import FollowUpQuestions from './FollowUpQuestions.vue'

const store = useProjectStore()

const props = defineProps({
  question: {
    type: Object,
    required: true
  },
  response: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['save', 'confirm', 'navigate-to-question'])

const localResponse = ref(props.response?.response || '')
const followUpData = ref(null)
const suggestLoading = ref(false)

// For multiselect, parse the response as an array
const selectedOptions = computed(() => {
  if (props.question.type !== 'multiselect') return []
  if (!localResponse.value) return []
  try {
    return JSON.parse(localResponse.value)
  } catch {
    return localResponse.value.split(',').map(s => s.trim()).filter(Boolean)
  }
})

// Watch for external changes to response
watch(() => props.response?.response, (newVal) => {
  if (newVal !== localResponse.value) {
    localResponse.value = newVal || ''
  }
})

const saveOnBlur = () => {
  if (localResponse.value !== props.response?.response) {
    emit('save', localResponse.value, props.response?.confirmed || false)
  }
}

const selectOption = (option) => {
  localResponse.value = option
  emit('save', option, false)
}

const toggleOption = (option) => {
  let current = [...selectedOptions.value]
  const index = current.indexOf(option)

  if (index > -1) {
    current.splice(index, 1)
  } else {
    current.push(option)
  }

  localResponse.value = JSON.stringify(current)
  emit('save', localResponse.value, false)
}

const confirm = async () => {
  emit('save', localResponse.value, true)
  emit('confirm', true)

  // Fetch follow-up questions after confirming
  if (store.currentProject?.id && localResponse.value) {
    try {
      const response = await questionsApi.getFollowUps(
        store.currentProject.id,
        props.question.id,
        {
          response: localResponse.value,
          question: props.question.question,
          include_ai: localResponse.value.length > 100  // Include AI for substantial responses
        }
      )
      followUpData.value = response.data
    } catch (error) {
      console.error('Failed to fetch follow-ups:', error)
    }
  }
}

const unconfirm = () => {
  emit('confirm', false)
  followUpData.value = null  // Clear follow-ups when editing
}

const getSmartSuggestion = async () => {
  if (!store.currentProject?.id) return

  suggestLoading.value = true
  try {
    const response = await questionsApi.smartSuggest(
      store.currentProject.id,
      props.question.id,
      props.question.question
    )

    if (response.data?.suggested_answer) {
      localResponse.value = response.data.suggested_answer
      emit('save', localResponse.value, false)
      store.showToast(`Suggestion (${response.data.confidence} confidence)`, 'success')
    }
  } catch (error) {
    console.error('Smart suggest failed:', error)
    store.showToast('Could not generate suggestion', 'error')
  } finally {
    suggestLoading.value = false
  }
}

const onFollowUpSaved = (data) => {
  // Refresh stats after saving follow-up
  store.fetchStats()
}
</script>

<style scoped>
.badges {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}
</style>
