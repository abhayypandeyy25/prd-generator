<template>
  <div class="features-tab">
    <!-- Header Card -->
    <div class="card" style="margin-bottom: 1.5rem;">
      <div class="card-header">
        <div>
          <h3 class="card-title">Product Features</h3>
          <span class="card-subtitle">
            Extract and select features from your context to guide AI responses
          </span>
        </div>
        <div class="header-actions">
          <button
            class="btn btn-secondary"
            @click="showAddModal = true"
          >
            + Add Manually
          </button>
          <button
            class="btn btn-primary"
            @click="extractFeatures"
            :disabled="store.contextFiles.length === 0 || store.loading"
          >
            {{ store.loading && store.loadingAction === 'extractFeatures' ? 'Extracting...' : 'Extract with AI' }}
          </button>
        </div>
      </div>

      <!-- No Context Warning -->
      <div v-if="store.contextFiles.length === 0" class="card-body">
        <div class="empty-state">
          <div class="empty-icon">📄</div>
          <h4>No Context Files</h4>
          <p>Upload context files first to extract features using AI.</p>
          <button class="btn btn-secondary" @click="store.setActiveTab('context')">
            Go to Context
          </button>
        </div>
      </div>
    </div>

    <!-- Active Features Section -->
    <div class="features-section">
      <div class="section-header">
        <h4 class="section-title">
          Active Features
          <span class="count-badge">{{ store.activeFeatures.length }}</span>
        </h4>
        <p class="section-subtitle">These features will be used when AI prefills questions</p>
      </div>

      <div v-if="store.activeFeatures.length === 0" class="empty-state-small">
        <p>No active features yet. Extract features from context or add them manually.</p>
      </div>

      <FeatureCard
        v-for="feature in store.activeFeatures"
        :key="feature.id"
        :feature="feature"
        @update="updateFeature"
        @toggle-selection="toggleFeatureSelection"
        @delete="deleteFeature"
      />
    </div>

    <!-- Parking Lot Section -->
    <div class="parking-lot-section" v-if="store.parkingLotFeatures.length > 0">
      <div class="parking-lot-header" @click="showParkingLot = !showParkingLot">
        <h4 class="section-title">
          Parking Lot
          <span class="count-badge muted">{{ store.parkingLotFeatures.length }}</span>
        </h4>
        <span class="toggle-icon">{{ showParkingLot ? '▼' : '▶' }}</span>
      </div>
      <p class="section-subtitle">Features saved for later consideration</p>

      <div v-if="showParkingLot" class="parking-lot-content">
        <FeatureCard
          v-for="feature in store.parkingLotFeatures"
          :key="feature.id"
          :feature="feature"
          @update="updateFeature"
          @toggle-selection="toggleFeatureSelection"
          @delete="deleteFeature"
        />
      </div>
    </div>

    <!-- Navigation -->
    <div class="navigation-footer" v-if="store.activeFeatures.length > 0">
      <div class="nav-info">
        <strong>{{ store.activeFeatures.length }}</strong> features selected for AI assistance
      </div>
      <button class="btn btn-primary btn-lg" @click="store.setActiveTab('questions')">
        Continue to Questions →
      </button>
    </div>

    <!-- Add Feature Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <h3 style="margin-bottom: 1rem;">Add Feature</h3>
        <input
          v-model="newFeatureName"
          type="text"
          placeholder="Feature name"
          class="modal-input"
          @keyup.enter="addFeature"
        />
        <textarea
          v-model="newFeatureDescription"
          placeholder="Brief description (optional)"
          class="modal-textarea"
          rows="3"
        ></textarea>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
          <button
            class="btn btn-primary"
            @click="addFeature"
            :disabled="!newFeatureName.trim()"
          >
            Add Feature
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import FeatureCard from './FeatureCard.vue'

const store = useProjectStore()

const showParkingLot = ref(true)
const showAddModal = ref(false)
const newFeatureName = ref('')
const newFeatureDescription = ref('')

const extractFeatures = async () => {
  try {
    await store.extractFeatures()
  } catch (error) {
    console.error('Failed to extract features:', error)
  }
}

const addFeature = async () => {
  if (!newFeatureName.value.trim()) return

  try {
    await store.createFeature(newFeatureName.value.trim(), newFeatureDescription.value.trim())
    newFeatureName.value = ''
    newFeatureDescription.value = ''
    showAddModal.value = false
  } catch (error) {
    console.error('Failed to add feature:', error)
  }
}

const updateFeature = async ({ id, name, description }) => {
  try {
    await store.updateFeature(id, { name, description })
  } catch (error) {
    console.error('Failed to update feature:', error)
  }
}

const toggleFeatureSelection = async (featureId, isSelected) => {
  try {
    await store.toggleFeatureSelection(featureId, isSelected)
  } catch (error) {
    console.error('Failed to toggle feature:', error)
  }
}

const deleteFeature = async (featureId) => {
  try {
    await store.deleteFeature(featureId)
  } catch (error) {
    console.error('Failed to delete feature:', error)
  }
}
</script>

<style scoped>
.features-tab {
  max-width: 900px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.card-subtitle {
  color: var(--gray-500);
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.features-section {
  margin-bottom: 2rem;
}

.section-header {
  margin-bottom: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--gray-700);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.section-subtitle {
  color: var(--gray-500);
  font-size: 0.8125rem;
  margin-top: 0.25rem;
}

.count-badge {
  background: var(--primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 1rem;
}

.count-badge.muted {
  background: var(--gray-400);
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h4 {
  margin-bottom: 0.5rem;
  color: var(--gray-700);
}

.empty-state p {
  color: var(--gray-500);
  margin-bottom: 1.5rem;
}

.empty-state-small {
  text-align: center;
  padding: 2rem;
  background: var(--gray-50);
  border-radius: var(--radius);
  color: var(--gray-500);
}

.parking-lot-section {
  margin-top: 2rem;
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius-lg);
  border: 1px dashed var(--gray-300);
}

.parking-lot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.toggle-icon {
  color: var(--gray-400);
  font-size: 0.75rem;
}

.parking-lot-content {
  margin-top: 1rem;
}

.navigation-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--gray-200);
}

.nav-info {
  color: var(--gray-600);
}

.btn-lg {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 450px;
  box-shadow: var(--shadow-lg);
}

.modal-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  margin-bottom: 0.75rem;
  font-size: 1rem;
}

.modal-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  margin-bottom: 1rem;
  font-size: 0.9375rem;
  resize: vertical;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
</style>
