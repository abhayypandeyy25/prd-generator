<template>
  <div class="template-selector">
    <div class="selector-header">
      <h3>Choose a PRD Template</h3>
      <p>Select a template that best fits your project needs</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading templates...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="btn btn-secondary" @click="fetchTemplates">Retry</button>
    </div>

    <div v-else class="templates-grid">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        :class="{
          selected: selectedTemplateId === template.id,
          default: template.is_default
        }"
        @click="selectTemplate(template)"
      >
        <div class="template-badge" v-if="template.is_default">
          Recommended
        </div>
        <div class="template-icon">
          {{ getTemplateIcon(template.name) }}
        </div>
        <h4 class="template-name">{{ template.name }}</h4>
        <p class="template-description">{{ template.description }}</p>
        <div class="template-meta">
          <span class="section-count">
            {{ template.section_count }} sections
          </span>
        </div>
        <div class="selected-indicator" v-if="selectedTemplateId === template.id">
          <span>✓ Selected</span>
        </div>
      </div>
    </div>

    <div class="selector-actions" v-if="!loading && !error">
      <button
        class="btn btn-secondary"
        @click="showCustomTemplateDialog = true"
      >
        + Create Custom Template
      </button>
    </div>

    <!-- Template Preview Modal -->
    <div v-if="previewTemplate" class="modal-overlay" @click.self="previewTemplate = null">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>{{ previewTemplate.name }}</h3>
          <button class="close-btn" @click="previewTemplate = null">×</button>
        </div>
        <div class="modal-body">
          <p class="template-desc">{{ previewTemplate.description }}</p>
          <h4>Sections</h4>
          <ul class="section-list">
            <li v-for="section in previewTemplate.sections" :key="section.id">
              <span class="section-name">{{ section.section_name }}</span>
              <span v-if="section.is_required" class="required-badge">Required</span>
            </li>
          </ul>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="previewTemplate = null">Close</button>
          <button class="btn btn-primary" @click="confirmSelect(previewTemplate)">
            Use This Template
          </button>
        </div>
      </div>
    </div>

    <!-- Custom Template Dialog -->
    <div v-if="showCustomTemplateDialog" class="modal-overlay" @click.self="showCustomTemplateDialog = false">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>Create Custom Template</h3>
          <button class="close-btn" @click="showCustomTemplateDialog = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Template Name</label>
            <input
              v-model="newTemplate.name"
              type="text"
              class="form-input"
              placeholder="e.g., My Company PRD"
            />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="newTemplate.description"
              class="form-input"
              rows="2"
              placeholder="Brief description of when to use this template"
            ></textarea>
          </div>
          <div class="form-group">
            <label>Sections</label>
            <div class="sections-editor">
              <div
                v-for="(section, index) in newTemplate.sections"
                :key="index"
                class="section-row"
              >
                <input
                  v-model="section.name"
                  type="text"
                  class="form-input section-input"
                  placeholder="Section name"
                />
                <label class="checkbox-label">
                  <input type="checkbox" v-model="section.required" />
                  Required
                </label>
                <button class="btn-icon" @click="removeSection(index)" title="Remove">
                  ×
                </button>
              </div>
              <button class="btn btn-sm btn-secondary" @click="addSection">
                + Add Section
              </button>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showCustomTemplateDialog = false">Cancel</button>
          <button
            class="btn btn-primary"
            @click="createCustomTemplate"
            :disabled="!newTemplate.name.trim() || newTemplate.sections.length === 0"
          >
            Create Template
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { templatesApi } from '../services/api'

const emit = defineEmits(['select', 'preview'])

const props = defineProps({
  selectedId: {
    type: String,
    default: null
  }
})

const templates = ref([])
const loading = ref(true)
const error = ref(null)
const selectedTemplateId = ref(props.selectedId)
const previewTemplate = ref(null)
const showCustomTemplateDialog = ref(false)

const newTemplate = ref({
  name: '',
  description: '',
  sections: [
    { name: 'Problem Statement', required: true },
    { name: 'Proposed Solution', required: true },
    { name: 'Success Metrics', required: false }
  ]
})

const templateIcons = {
  'Lean PRD': '🚀',
  'Detailed PRD': '📋',
  'Technical Spec': '⚙️',
  'One-Pager': '📄',
  'Feature Brief': '✨'
}

const getTemplateIcon = (name) => {
  for (const [key, icon] of Object.entries(templateIcons)) {
    if (name.includes(key)) return icon
  }
  return '📝'
}

const fetchTemplates = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await templatesApi.list()
    templates.value = response.data || []

    // Auto-select default template if none selected
    if (!selectedTemplateId.value && templates.value.length > 0) {
      const defaultTemplate = templates.value.find(t => t.is_default)
      if (defaultTemplate) {
        selectedTemplateId.value = defaultTemplate.id
        emit('select', defaultTemplate)
      }
    }
  } catch (err) {
    console.error('Failed to fetch templates:', err)
    error.value = 'Failed to load templates. Please try again.'
  } finally {
    loading.value = false
  }
}

const selectTemplate = async (template) => {
  // Fetch full template details for preview
  try {
    const response = await templatesApi.get(template.id)
    previewTemplate.value = response.data
  } catch (err) {
    console.error('Failed to fetch template details:', err)
    // Just select without preview
    confirmSelect(template)
  }
}

const confirmSelect = (template) => {
  selectedTemplateId.value = template.id
  emit('select', template)
  previewTemplate.value = null
}

const addSection = () => {
  newTemplate.value.sections.push({ name: '', required: false })
}

const removeSection = (index) => {
  newTemplate.value.sections.splice(index, 1)
}

const createCustomTemplate = async () => {
  try {
    const data = {
      name: newTemplate.value.name.trim(),
      description: newTemplate.value.description.trim(),
      sections: newTemplate.value.sections
        .filter(s => s.name.trim())
        .map((s, i) => ({
          name: s.name.trim(),
          order: i + 1,
          required: s.required
        }))
    }

    const response = await templatesApi.create(data)

    if (response.data?.template_id) {
      // Refresh templates list
      await fetchTemplates()

      // Select the new template
      const newTemplateData = templates.value.find(t => t.id === response.data.template_id)
      if (newTemplateData) {
        confirmSelect(newTemplateData)
      }
    }

    showCustomTemplateDialog.value = false

    // Reset form
    newTemplate.value = {
      name: '',
      description: '',
      sections: [
        { name: 'Problem Statement', required: true },
        { name: 'Proposed Solution', required: true },
        { name: 'Success Metrics', required: false }
      ]
    }
  } catch (err) {
    console.error('Failed to create template:', err)
    error.value = 'Failed to create template. Please try again.'
  }
}

onMounted(() => {
  fetchTemplates()
})
</script>

<style scoped>
.template-selector {
  padding: 1rem 0;
}

.selector-header {
  text-align: center;
  margin-bottom: 2rem;
}

.selector-header h3 {
  margin: 0 0 0.5rem;
  color: var(--gray-800);
}

.selector-header p {
  margin: 0;
  color: var(--gray-500);
}

.loading-state,
.error-state {
  text-align: center;
  padding: 3rem;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.template-card {
  position: relative;
  background: white;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.template-card:hover {
  border-color: var(--gray-300);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.template-card.selected {
  border-color: var(--primary);
  background: var(--primary-light);
}

.template-card.default {
  border-color: var(--primary);
}

.template-badge {
  position: absolute;
  top: -10px;
  right: 12px;
  background: var(--primary);
  color: white;
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.25rem 0.5rem;
  border-radius: 100px;
  text-transform: uppercase;
}

.template-icon {
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.template-name {
  margin: 0 0 0.5rem;
  font-size: 1.125rem;
  color: var(--gray-800);
}

.template-description {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  color: var(--gray-600);
  line-height: 1.5;
}

.template-meta {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.section-count {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.selected-indicator {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  color: var(--primary);
  font-size: 0.875rem;
  font-weight: 600;
}

.selector-actions {
  text-align: center;
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
  z-index: 100;
}

.modal-dialog {
  background: white;
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--gray-200);
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  font-size: 1.5rem;
  color: var(--gray-500);
  cursor: pointer;
  border-radius: var(--radius);
}

.close-btn:hover {
  background: var(--gray-100);
}

.modal-body {
  padding: 1.5rem;
}

.template-desc {
  color: var(--gray-600);
  margin-bottom: 1.5rem;
}

.modal-body h4 {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  color: var(--gray-700);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.section-list li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--gray-100);
}

.section-list li:last-child {
  border-bottom: none;
}

.section-name {
  flex: 1;
  color: var(--gray-700);
}

.required-badge {
  font-size: 0.6875rem;
  background: var(--primary-light);
  color: var(--primary);
  padding: 0.125rem 0.375rem;
  border-radius: 100px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--gray-200);
}

/* Form styles */
.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.375rem;
  font-weight: 500;
  color: var(--gray-700);
}

.form-input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 0.9375rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.sections-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.section-input {
  flex: 1;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: var(--gray-600);
  white-space: nowrap;
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--gray-400);
  font-size: 1.25rem;
  cursor: pointer;
  border-radius: var(--radius);
}

.btn-icon:hover {
  background: var(--gray-100);
  color: var(--error);
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius);
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
}

.btn-secondary {
  background: white;
  border: 1px solid var(--gray-300);
  color: var(--gray-700);
}

.btn-secondary:hover {
  background: var(--gray-100);
}

.btn-primary {
  background: var(--primary);
  border: 1px solid var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark);
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .templates-grid {
    grid-template-columns: 1fr;
  }
}
</style>
