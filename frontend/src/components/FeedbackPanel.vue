<template>
  <div class="feedback-panel">
    <!-- Feedback Header -->
    <div class="feedback-header">
      <h3>PRD Feedback & Improvement</h3>
      <button class="btn btn-sm btn-ghost" @click="$emit('close')">
        ✕
      </button>
    </div>

    <!-- Rating Section -->
    <div class="rating-section">
      <h4>Rate This PRD</h4>
      <div class="star-rating">
        <button
          v-for="star in 5"
          :key="star"
          class="star-btn"
          :class="{ filled: star <= (hoverRating || selectedRating) }"
          @mouseenter="hoverRating = star"
          @mouseleave="hoverRating = 0"
          @click="selectedRating = star"
        >
          ★
        </button>
      </div>
      <p class="rating-label">{{ ratingLabel }}</p>
    </div>

    <!-- Section Rating -->
    <div class="section-rating">
      <label>What section needs improvement?</label>
      <select v-model="selectedSection">
        <option value="">Select a section (optional)</option>
        <option value="Executive Summary">Executive Summary</option>
        <option value="Problem Statement">Problem Statement</option>
        <option value="User Personas">User Personas</option>
        <option value="Features">Features & Requirements</option>
        <option value="Technical">Technical Requirements</option>
        <option value="Timeline">Timeline & Milestones</option>
        <option value="Metrics">Success Metrics</option>
        <option value="Other">Other</option>
      </select>
    </div>

    <!-- Feedback Text -->
    <div class="feedback-text">
      <label>How can we improve?</label>
      <textarea
        v-model="feedbackText"
        placeholder="What would make this PRD better? Be specific..."
        rows="4"
      ></textarea>
    </div>

    <!-- Submit Button -->
    <button
      class="btn btn-primary"
      @click="submitFeedback"
      :disabled="!selectedRating || submitting"
    >
      {{ submitting ? 'Submitting...' : 'Submit Feedback' }}
    </button>

    <!-- Feedback Stats -->
    <div v-if="stats" class="stats-section">
      <h4>Feedback Summary</h4>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-value">{{ stats.total_feedback }}</span>
          <span class="stat-label">Total Reviews</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.average_rating ? stats.average_rating.toFixed(1) : '-' }}</span>
          <span class="stat-label">Avg Rating</span>
        </div>
      </div>

      <!-- Rating Distribution -->
      <div v-if="stats.rating_distribution && Object.keys(stats.rating_distribution).length" class="distribution">
        <div
          v-for="(count, rating) in stats.rating_distribution"
          :key="rating"
          class="distribution-bar"
        >
          <span class="dist-label">{{ rating }} ★</span>
          <div class="dist-track">
            <div
              class="dist-fill"
              :style="{ width: (count / stats.total_feedback * 100) + '%' }"
            ></div>
          </div>
          <span class="dist-count">{{ count }}</span>
        </div>
      </div>

      <!-- Improvement Areas -->
      <div v-if="stats.patterns?.improvement_areas?.length" class="improvement-areas">
        <h5>Areas for Improvement</h5>
        <ul>
          <li v-for="area in stats.patterns.improvement_areas" :key="area">
            {{ area }}
          </li>
        </ul>
      </div>
    </div>

    <!-- AI Suggestions -->
    <div class="ai-suggestions-section">
      <div class="suggestions-header">
        <h4>AI Improvement Suggestions</h4>
        <button
          class="btn btn-sm btn-secondary"
          @click="fetchSuggestions"
          :disabled="suggestionsLoading"
        >
          {{ suggestionsLoading ? 'Loading...' : '🤖 Get Suggestions' }}
        </button>
      </div>

      <div v-if="suggestions" class="suggestions-content">
        <div v-if="suggestions.priority_improvements?.length" class="suggestion-group">
          <h5>Priority Improvements</h5>
          <ol>
            <li v-for="(imp, idx) in suggestions.priority_improvements" :key="idx">
              {{ imp }}
            </li>
          </ol>
        </div>

        <div v-if="suggestions.missing_elements?.length" class="suggestion-group">
          <h5>Missing Elements</h5>
          <ul>
            <li v-for="(elem, idx) in suggestions.missing_elements" :key="idx">
              {{ elem }}
            </li>
          </ul>
        </div>

        <button
          class="btn btn-primary"
          @click="applyImprovements"
          :disabled="improving"
        >
          {{ improving ? 'Improving...' : '✨ Apply AI Improvements' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { feedbackApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'

const store = useProjectStore()

const emit = defineEmits(['close', 'improved'])

const selectedRating = ref(0)
const hoverRating = ref(0)
const selectedSection = ref('')
const feedbackText = ref('')
const submitting = ref(false)
const stats = ref(null)
const suggestions = ref(null)
const suggestionsLoading = ref(false)
const improving = ref(false)

const ratingLabel = computed(() => {
  const rating = hoverRating.value || selectedRating.value
  const labels = {
    1: 'Needs major work',
    2: 'Below expectations',
    3: 'Meets basic needs',
    4: 'Good quality',
    5: 'Excellent!'
  }
  return labels[rating] || 'Select a rating'
})

onMounted(async () => {
  await fetchStats()
})

const fetchStats = async () => {
  if (!store.currentProject?.id) return

  try {
    const response = await feedbackApi.getStats(store.currentProject.id)
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

const submitFeedback = async () => {
  if (!store.currentProject?.id || !selectedRating.value) return

  submitting.value = true
  try {
    await feedbackApi.ratePRD(
      store.currentProject.id,
      selectedRating.value,
      feedbackText.value,
      selectedSection.value || null
    )

    store.showToast('Thank you for your feedback!', 'success')

    // Reset form
    selectedRating.value = 0
    feedbackText.value = ''
    selectedSection.value = ''

    // Refresh stats
    await fetchStats()
  } catch (error) {
    console.error('Failed to submit feedback:', error)
    store.showToast('Failed to submit feedback', 'error')
  } finally {
    submitting.value = false
  }
}

const fetchSuggestions = async () => {
  if (!store.currentProject?.id) return

  suggestionsLoading.value = true
  try {
    const response = await feedbackApi.getSuggestions(store.currentProject.id)
    suggestions.value = response.data
  } catch (error) {
    console.error('Failed to fetch suggestions:', error)
    store.showToast('Failed to get suggestions', 'error')
  } finally {
    suggestionsLoading.value = false
  }
}

const applyImprovements = async () => {
  if (!store.currentProject?.id) return

  improving.value = true
  try {
    await feedbackApi.improveWithFeedback(store.currentProject.id)
    store.showToast('PRD improved! Refreshing...', 'success')

    // Refresh PRD
    await store.fetchPRD()
    emit('improved')
  } catch (error) {
    console.error('Failed to apply improvements:', error)
    store.showToast('Failed to apply improvements', 'error')
  } finally {
    improving.value = false
  }
}
</script>

<style scoped>
.feedback-panel {
  padding: 1.5rem;
  background: white;
  border-radius: var(--radius-lg);
  margin-top: 1.5rem;
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.feedback-header h3 {
  margin: 0;
  font-size: 1.125rem;
  color: var(--gray-800);
}

.btn-ghost {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--gray-400);
  cursor: pointer;
  padding: 0.25rem;
}

.btn-ghost:hover {
  color: var(--gray-600);
}

.rating-section {
  text-align: center;
  margin-bottom: 1.5rem;
}

.rating-section h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9375rem;
  color: var(--gray-700);
}

.star-rating {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.star-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: var(--gray-300);
  cursor: pointer;
  transition: all 0.2s;
}

.star-btn:hover,
.star-btn.filled {
  color: #fbbf24;
  transform: scale(1.1);
}

.rating-label {
  margin: 0.5rem 0 0 0;
  font-size: 0.875rem;
  color: var(--gray-500);
}

.section-rating,
.feedback-text {
  margin-bottom: 1rem;
}

.section-rating label,
.feedback-text label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--gray-700);
}

.section-rating select,
.feedback-text textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  font-size: 0.875rem;
}

.section-rating select:focus,
.feedback-text textarea:focus {
  outline: none;
  border-color: var(--primary);
}

.feedback-text textarea {
  resize: vertical;
  min-height: 100px;
}

.stats-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--gray-200);
}

.stats-section h4 {
  margin: 0 0 1rem 0;
  font-size: 0.9375rem;
  color: var(--gray-700);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius);
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
}

.distribution {
  margin-bottom: 1rem;
}

.distribution-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
}

.dist-label {
  width: 30px;
  font-size: 0.75rem;
  color: var(--gray-600);
}

.dist-track {
  flex: 1;
  height: 8px;
  background: var(--gray-200);
  border-radius: 4px;
  overflow: hidden;
}

.dist-fill {
  height: 100%;
  background: #fbbf24;
  transition: width 0.3s;
}

.dist-count {
  width: 20px;
  font-size: 0.75rem;
  color: var(--gray-500);
  text-align: right;
}

.improvement-areas {
  margin-top: 1rem;
}

.improvement-areas h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.8125rem;
  color: var(--gray-600);
  text-transform: uppercase;
}

.improvement-areas ul {
  margin: 0;
  padding-left: 1.25rem;
}

.improvement-areas li {
  font-size: 0.875rem;
  color: var(--gray-700);
  margin-bottom: 0.375rem;
}

.ai-suggestions-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--gray-200);
}

.suggestions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.suggestions-header h4 {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--gray-700);
}

.suggestions-content {
  background: var(--gray-50);
  border-radius: var(--radius);
  padding: 1rem;
}

.suggestion-group {
  margin-bottom: 1rem;
}

.suggestion-group:last-of-type {
  margin-bottom: 1rem;
}

.suggestion-group h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.8125rem;
  color: var(--gray-600);
  text-transform: uppercase;
}

.suggestion-group ol,
.suggestion-group ul {
  margin: 0;
  padding-left: 1.25rem;
}

.suggestion-group li {
  font-size: 0.875rem;
  color: var(--gray-700);
  margin-bottom: 0.375rem;
}
</style>
