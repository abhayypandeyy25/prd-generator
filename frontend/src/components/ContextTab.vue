<template>
  <div class="context-tab">
    <!-- Upload Section -->
    <div class="card" style="margin-bottom: 1.5rem;">
      <div class="card-header">
        <h3 class="card-title">Upload Context</h3>
        <span style="color: var(--gray-500); font-size: 0.875rem;">
          Add emails, docs, meeting notes, and other context
        </span>
      </div>
      <div class="card-body">
        <div
          class="file-uploader"
          :class="{ 'drag-over': isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
        >
          <div class="file-uploader-icon">📁</div>
          <p class="file-uploader-text">
            Drag & drop files here or click to browse
          </p>
          <p class="file-uploader-hint">
            Supports: PDF, Word, Excel, TXT, Markdown, Email (.eml)
          </p>
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".txt,.md,.pdf,.docx,.xlsx,.csv,.eml"
            style="display: none;"
            @change="handleFileSelect"
          >
        </div>

        <!-- Uploaded Files List -->
        <div v-if="store.contextFiles.length > 0" class="file-list">
          <div v-for="file in store.contextFiles" :key="file.id" class="file-item">
            <div class="file-icon">
              {{ getFileIcon(file.file_type) }}
            </div>
            <div class="file-info">
              <div class="file-name">{{ file.file_name }}</div>
              <div class="file-meta">
                {{ file.file_type.toUpperCase() }} •
                {{ (file.extracted_text || '').length.toLocaleString() }} chars extracted
              </div>
            </div>
            <button class="btn btn-secondary" @click="togglePreview(file.id)">
              {{ expandedFile === file.id ? 'Hide' : 'Preview' }}
            </button>
            <button class="btn btn-danger" @click="deleteFile(file.id)">
              Delete
            </button>
          </div>

          <!-- Expanded Preview -->
          <div v-if="expandedFile" class="file-preview">
            <h4>Extracted Text Preview</h4>
            <pre>{{ getPreviewText(expandedFile) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Context Summary -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Context Summary</h3>
        <button
          class="btn btn-primary"
          @click="goToFeatures"
          :disabled="store.contextFiles.length === 0"
        >
          Continue to Features →
        </button>
      </div>
      <div class="card-body">
        <div v-if="store.contextFiles.length === 0" style="text-align: center; padding: 2rem; color: var(--gray-500);">
          No context files uploaded yet. Upload files to get started.
        </div>
        <div v-else>
          <div class="summary-stats">
            <div class="stat-item">
              <div class="stat-value">{{ store.contextFiles.length }}</div>
              <div class="stat-label">Files Uploaded</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ totalChars.toLocaleString() }}</div>
              <div class="stat-label">Characters Extracted</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ fileTypes.join(', ') }}</div>
              <div class="stat-label">File Types</div>
            </div>
          </div>

          <div style="margin-top: 1.5rem;">
            <h4 style="margin-bottom: 0.75rem;">Files Included:</h4>
            <ul style="list-style: none; padding: 0;">
              <li v-for="file in store.contextFiles" :key="file.id" style="padding: 0.5rem 0; border-bottom: 1px solid var(--gray-100);">
                📄 {{ file.file_name }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Context Quality Analysis -->
    <ContextAnalysis v-if="store.contextFiles.length > 0" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useProjectStore } from '../stores/projectStore'
import ContextAnalysis from './ContextAnalysis.vue'

const store = useProjectStore()

const fileInput = ref(null)
const isDragging = ref(false)
const expandedFile = ref(null)

const totalChars = computed(() => {
  return store.contextFiles.reduce((sum, f) => sum + (f.extracted_text || '').length, 0)
})

const fileTypes = computed(() => {
  const types = new Set(store.contextFiles.map(f => f.file_type.toUpperCase()))
  return Array.from(types)
})

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    await store.uploadFiles(files)
    event.target.value = '' // Reset input
  }
}

const handleDrop = async (event) => {
  isDragging.value = false
  const files = Array.from(event.dataTransfer.files)
  if (files.length > 0) {
    await store.uploadFiles(files)
  }
}

const getFileIcon = (type) => {
  const icons = {
    pdf: '📕',
    docx: '📘',
    xlsx: '📗',
    txt: '📄',
    md: '📝',
    csv: '📊',
    eml: '📧'
  }
  return icons[type] || '📄'
}

const togglePreview = (fileId) => {
  expandedFile.value = expandedFile.value === fileId ? null : fileId
}

const getPreviewText = (fileId) => {
  const file = store.contextFiles.find(f => f.id === fileId)
  if (!file) return ''
  const text = file.extracted_text || ''
  return text.substring(0, 2000) + (text.length > 2000 ? '\n\n... (truncated)' : '')
}

const deleteFile = async (fileId) => {
  if (confirm('Are you sure you want to delete this file?')) {
    await store.deleteContextFile(fileId)
  }
}

const goToFeatures = () => {
  store.setActiveTab('features')
}
</script>

<style scoped>
.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--gray-500);
  margin-top: 0.25rem;
}

.file-preview {
  margin-top: 1rem;
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius);
  border: 1px solid var(--gray-200);
}

.file-preview h4 {
  margin-bottom: 0.75rem;
  color: var(--gray-700);
}

.file-preview pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.8125rem;
  color: var(--gray-600);
  max-height: 300px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .summary-stats {
    grid-template-columns: 1fr;
  }
}
</style>
