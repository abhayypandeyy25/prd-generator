<template>
  <div class="feature-card" :class="{ 'parking-lot': !feature.is_selected }">
    <div class="feature-header">
      <div v-if="!isEditing" class="feature-name">
        {{ feature.name }}
        <span v-if="feature.is_ai_generated" class="ai-badge">AI</span>
      </div>
      <input
        v-else
        v-model="editName"
        class="feature-name-input"
        placeholder="Feature name"
        @keyup.enter="saveEdit"
      />
    </div>

    <div v-if="!isEditing" class="feature-description">
      {{ feature.description || 'No description' }}
    </div>
    <textarea
      v-else
      v-model="editDescription"
      class="feature-description-input"
      placeholder="Feature description"
      rows="2"
    ></textarea>

    <div class="feature-actions">
      <template v-if="!isEditing">
        <button class="btn btn-sm btn-secondary" @click="startEdit">
          Edit
        </button>
        <button
          class="btn btn-sm"
          :class="feature.is_selected ? 'btn-warning' : 'btn-primary'"
          @click="toggleSelection"
        >
          {{ feature.is_selected ? 'Park' : 'Activate' }}
        </button>
        <button class="btn btn-sm btn-danger" @click="confirmDelete">
          Delete
        </button>
      </template>
      <template v-else>
        <button class="btn btn-sm btn-primary" @click="saveEdit">
          Save
        </button>
        <button class="btn btn-sm btn-secondary" @click="cancelEdit">
          Cancel
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  feature: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update', 'toggle-selection', 'delete'])

const isEditing = ref(false)
const editName = ref('')
const editDescription = ref('')

const startEdit = () => {
  editName.value = props.feature.name
  editDescription.value = props.feature.description || ''
  isEditing.value = true
}

const saveEdit = () => {
  if (!editName.value.trim()) return

  emit('update', {
    id: props.feature.id,
    name: editName.value.trim(),
    description: editDescription.value.trim()
  })
  isEditing.value = false
}

const cancelEdit = () => {
  isEditing.value = false
}

const toggleSelection = () => {
  emit('toggle-selection', props.feature.id, !props.feature.is_selected)
}

const confirmDelete = () => {
  if (confirm(`Delete "${props.feature.name}"?`)) {
    emit('delete', props.feature.id)
  }
}
</script>

<style scoped>
.feature-card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
  transition: all 0.2s;
}

.feature-card:hover {
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.feature-card.parking-lot {
  background: var(--gray-50);
  border-style: dashed;
  opacity: 0.85;
}

.feature-header {
  margin-bottom: 0.5rem;
}

.feature-name {
  font-weight: 600;
  color: var(--gray-800);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.feature-name-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 1rem;
}

.ai-badge {
  background: var(--primary-light, #e0f2fe);
  color: var(--primary, #0284c7);
  font-size: 0.625rem;
  font-weight: 600;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  text-transform: uppercase;
}

.feature-description {
  color: var(--gray-600);
  font-size: 0.9375rem;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.feature-description-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 0.9375rem;
  resize: vertical;
  margin-bottom: 0.5rem;
}

.feature-actions {
  display: flex;
  gap: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--gray-100);
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
}

.btn-warning {
  background: var(--yellow-100, #fef3c7);
  color: var(--yellow-800, #92400e);
  border: 1px solid var(--yellow-300, #fcd34d);
}

.btn-warning:hover {
  background: var(--yellow-200, #fde68a);
}

.btn-danger {
  background: transparent;
  color: var(--red-600, #dc2626);
  border: 1px solid var(--red-200, #fecaca);
}

.btn-danger:hover {
  background: var(--red-50, #fef2f2);
}
</style>
