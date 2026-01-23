<template>
  <div class="prd-editor">
    <!-- Editor Toolbar -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <button
          class="toolbar-btn"
          :class="{ active: viewMode === 'edit' }"
          @click="viewMode = 'edit'"
          title="Edit mode"
        >
          <span class="icon">✏️</span> Edit
        </button>
        <button
          class="toolbar-btn"
          :class="{ active: viewMode === 'preview' }"
          @click="viewMode = 'preview'"
          title="Preview mode"
        >
          <span class="icon">👁️</span> Preview
        </button>
        <button
          class="toolbar-btn"
          :class="{ active: viewMode === 'split' }"
          @click="viewMode = 'split'"
          title="Split view"
        >
          <span class="icon">📊</span> Split
        </button>
      </div>

      <div class="toolbar-center">
        <span v-if="hasUnsavedChanges" class="unsaved-indicator">
          <span class="dot"></span> Unsaved changes
        </span>
        <span v-else-if="lastSaved" class="saved-indicator">
          Saved {{ formatTime(lastSaved) }}
        </span>
      </div>

      <div class="toolbar-right">
        <button
          class="toolbar-btn"
          @click="showVersionDialog = true"
          title="Save as version"
        >
          <span class="icon">💾</span> Save Version
        </button>
        <button
          class="toolbar-btn"
          @click="showHistoryPanel = !showHistoryPanel"
          :class="{ active: showHistoryPanel }"
          title="Version history"
        >
          <span class="icon">📜</span> History
        </button>
        <button
          class="toolbar-btn primary"
          @click="saveChanges"
          :disabled="!hasUnsavedChanges || isSaving"
          title="Save changes"
        >
          {{ isSaving ? 'Saving...' : 'Save' }}
        </button>
      </div>
    </div>

    <!-- Main Editor Area -->
    <div class="editor-container" :class="[viewMode]">
      <!-- Edit Panel -->
      <div v-if="viewMode !== 'preview'" class="edit-panel">
        <div class="section-nav">
          <button
            v-for="section in detectedSections"
            :key="section.id"
            class="section-btn"
            :class="{ active: activeSection === section.id }"
            @click="scrollToSection(section)"
          >
            {{ section.title }}
          </button>
        </div>
        <textarea
          ref="editorRef"
          v-model="editContent"
          class="markdown-editor"
          placeholder="Start writing your PRD..."
          @input="onContentChange"
          @keydown="handleKeydown"
        ></textarea>
      </div>

      <!-- Preview Panel -->
      <div v-if="viewMode !== 'edit'" class="preview-panel">
        <div class="preview-content" v-html="renderedPreview"></div>
      </div>

      <!-- History Panel -->
      <div v-if="showHistoryPanel" class="history-panel">
        <div class="history-header">
          <h3>Version History</h3>
          <button class="close-btn" @click="showHistoryPanel = false">×</button>
        </div>
        <div class="history-list">
          <div
            v-for="snapshot in store.prdHistory"
            :key="snapshot.id"
            class="history-item"
            :class="{ major: snapshot.is_major_version }"
          >
            <div class="history-info">
              <span class="version-name">
                {{ snapshot.version_name || formatDate(snapshot.created_at) }}
              </span>
              <span class="version-date">{{ formatDate(snapshot.created_at) }}</span>
              <span v-if="snapshot.change_summary" class="version-summary">
                {{ snapshot.change_summary }}
              </span>
            </div>
            <div class="history-actions">
              <button class="btn-sm" @click="previewVersion(snapshot)">Preview</button>
              <button class="btn-sm primary" @click="restoreVersion(snapshot)">Restore</button>
            </div>
          </div>
          <div v-if="store.prdHistory.length === 0" class="no-history">
            No saved versions yet
          </div>
        </div>
      </div>
    </div>

    <!-- Section Regeneration Menu -->
    <div v-if="showSectionMenu" class="section-menu" :style="sectionMenuPosition">
      <div class="section-menu-header">Regenerate Section</div>
      <button
        v-for="section in detectedSections"
        :key="section.id"
        class="section-menu-item"
        @click="regenerateSection(section.title)"
      >
        🔄 {{ section.title }}
      </button>
    </div>

    <!-- Save Version Dialog -->
    <div v-if="showVersionDialog" class="modal-overlay" @click.self="showVersionDialog = false">
      <div class="modal-dialog">
        <h3>Save Version</h3>
        <div class="form-group">
          <label>Version Name</label>
          <input
            v-model="versionName"
            type="text"
            placeholder="e.g., v1.0, Initial Draft, Post-Review"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label>Change Summary (optional)</label>
          <textarea
            v-model="changeSummary"
            placeholder="Brief description of changes..."
            class="form-input"
            rows="3"
          ></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn secondary" @click="showVersionDialog = false">Cancel</button>
          <button
            class="btn primary"
            @click="saveVersion"
            :disabled="!versionName.trim()"
          >
            Save Version
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Version Dialog -->
    <div v-if="previewingVersion" class="modal-overlay" @click.self="previewingVersion = null">
      <div class="modal-dialog large">
        <div class="modal-header">
          <h3>{{ previewingVersion.version_name || 'Version Preview' }}</h3>
          <button class="close-btn" @click="previewingVersion = null">×</button>
        </div>
        <div class="preview-content modal-body" v-html="renderedPreviewVersion"></div>
        <div class="modal-actions">
          <button class="btn secondary" @click="previewingVersion = null">Close</button>
          <button class="btn primary" @click="restoreVersion(previewingVersion)">
            Restore This Version
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import { useProjectStore } from '../stores/projectStore'

const props = defineProps({
  initialContent: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['save', 'close'])

const store = useProjectStore()
const editorRef = ref(null)

// Editor state
const editContent = ref(props.initialContent || '')
const viewMode = ref('split') // 'edit', 'preview', 'split'
const hasUnsavedChanges = ref(false)
const isSaving = ref(false)
const lastSaved = ref(null)
const activeSection = ref(null)

// History panel
const showHistoryPanel = ref(false)

// Version dialog
const showVersionDialog = ref(false)
const versionName = ref('')
const changeSummary = ref('')

// Section menu
const showSectionMenu = ref(false)
const sectionMenuPosition = ref({ top: '0px', left: '0px' })

// Version preview
const previewingVersion = ref(null)

// Configure marked
marked.setOptions({
  gfm: true,
  breaks: true
})

// Computed
const renderedPreview = computed(() => {
  if (!editContent.value) return ''
  return marked(editContent.value)
})

const renderedPreviewVersion = computed(() => {
  if (!previewingVersion.value?.snapshot_content) return ''
  return marked(previewingVersion.value.snapshot_content)
})

const detectedSections = computed(() => {
  const sections = []
  const lines = editContent.value.split('\n')
  let lineNumber = 0

  for (const line of lines) {
    // Match ## headings (H2)
    const match = line.match(/^##\s+(.+)/)
    if (match) {
      sections.push({
        id: `section-${sections.length}`,
        title: match[1].trim(),
        line: lineNumber
      })
    }
    lineNumber++
  }

  return sections
})

// Watch for initial content changes
watch(() => props.initialContent, (newContent) => {
  if (newContent && !hasUnsavedChanges.value) {
    editContent.value = newContent
  }
})

// Watch for store PRD changes
watch(() => store.prd, (newPrd) => {
  if (newPrd && !hasUnsavedChanges.value) {
    editContent.value = newPrd
  }
})

// Methods
const onContentChange = () => {
  hasUnsavedChanges.value = editContent.value !== (store.prd || '')
}

const handleKeydown = (e) => {
  // Ctrl/Cmd + S to save
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault()
    saveChanges()
  }
}

const saveChanges = async () => {
  if (!hasUnsavedChanges.value || isSaving.value) return

  isSaving.value = true
  try {
    await store.editPRD(editContent.value)
    hasUnsavedChanges.value = false
    lastSaved.value = new Date()
    emit('save', editContent.value)
  } catch (error) {
    console.error('Failed to save:', error)
  } finally {
    isSaving.value = false
  }
}

const scrollToSection = (section) => {
  activeSection.value = section.id
  if (editorRef.value) {
    const lines = editContent.value.split('\n')
    let charCount = 0
    for (let i = 0; i < section.line; i++) {
      charCount += lines[i].length + 1 // +1 for newline
    }
    editorRef.value.setSelectionRange(charCount, charCount)
    editorRef.value.focus()

    // Scroll the line into view
    const lineHeight = 24 // approximate line height
    editorRef.value.scrollTop = section.line * lineHeight - 100
  }
}

const regenerateSection = async (sectionTitle) => {
  showSectionMenu.value = false
  try {
    await store.regeneratePRDSection(sectionTitle)
    editContent.value = store.prd || editContent.value
    hasUnsavedChanges.value = false
  } catch (error) {
    console.error('Failed to regenerate section:', error)
  }
}

const saveVersion = async () => {
  if (!versionName.value.trim()) return

  try {
    await store.savePRDVersion(versionName.value.trim(), changeSummary.value.trim())
    showVersionDialog.value = false
    versionName.value = ''
    changeSummary.value = ''
  } catch (error) {
    console.error('Failed to save version:', error)
  }
}

const previewVersion = (snapshot) => {
  previewingVersion.value = snapshot
}

const restoreVersion = async (snapshot) => {
  try {
    await store.restorePRDVersion(snapshot.id)
    editContent.value = store.prd || editContent.value
    hasUnsavedChanges.value = false
    previewingVersion.value = null
  } catch (error) {
    console.error('Failed to restore version:', error)
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (date) => {
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  return formatDate(date)
}

// Load history on mount
onMounted(async () => {
  if (store.currentProject) {
    await store.fetchPRDHistory()
  }
  if (store.prd) {
    editContent.value = store.prd
  }
})
</script>

<style scoped>
.prd-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
  flex-wrap: wrap;
  gap: 0.5rem;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 0.5rem;
}

.toolbar-center {
  flex: 1;
  text-align: center;
  font-size: 0.875rem;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  background: white;
  color: var(--gray-700);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.toolbar-btn:hover {
  background: var(--gray-100);
  border-color: var(--gray-400);
}

.toolbar-btn.active {
  background: var(--primary-light);
  border-color: var(--primary);
  color: var(--primary);
}

.toolbar-btn.primary {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.toolbar-btn.primary:hover {
  background: var(--primary-dark);
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon {
  font-size: 1rem;
}

.unsaved-indicator {
  color: var(--warning);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.unsaved-indicator .dot {
  width: 8px;
  height: 8px;
  background: var(--warning);
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.saved-indicator {
  color: var(--gray-500);
}

.editor-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.editor-container.edit .edit-panel {
  width: 100%;
}

.editor-container.preview .preview-panel {
  width: 100%;
}

.editor-container.split .edit-panel,
.editor-container.split .preview-panel {
  width: 50%;
}

.edit-panel {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--gray-200);
}

.section-nav {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
  overflow-x: auto;
  flex-shrink: 0;
}

.section-btn {
  padding: 0.375rem 0.75rem;
  border: none;
  background: none;
  color: var(--gray-600);
  font-size: 0.75rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  white-space: nowrap;
}

.section-btn:hover {
  background: var(--gray-100);
}

.section-btn.active {
  background: var(--primary-light);
  color: var(--primary);
}

.markdown-editor {
  flex: 1;
  width: 100%;
  padding: 1.5rem;
  border: none;
  resize: none;
  font-family: 'SF Mono', Monaco, 'Courier New', monospace;
  font-size: 0.9375rem;
  line-height: 1.6;
  color: var(--gray-800);
}

.markdown-editor:focus {
  outline: none;
}

.preview-panel {
  overflow-y: auto;
}

.preview-content {
  padding: 2rem;
}

/* Markdown preview styles */
.preview-content :deep(h1) {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  color: var(--gray-900);
  border-bottom: 3px solid var(--primary);
  padding-bottom: 0.5rem;
}

.preview-content :deep(h2) {
  font-size: 1.5rem;
  margin-top: 2.5rem;
  margin-bottom: 1rem;
  color: var(--gray-800);
  border-bottom: 2px solid var(--gray-200);
  padding-bottom: 0.5rem;
}

.preview-content :deep(h3) {
  font-size: 1.25rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: var(--gray-700);
}

.preview-content :deep(p) {
  margin-bottom: 1rem;
  line-height: 1.7;
}

.preview-content :deep(ul),
.preview-content :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.preview-content :deep(li) {
  margin-bottom: 0.5rem;
  line-height: 1.6;
}

.preview-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
}

.preview-content :deep(th),
.preview-content :deep(td) {
  padding: 0.75rem 1rem;
  border: 1px solid var(--gray-200);
  text-align: left;
}

.preview-content :deep(th) {
  background: var(--gray-50);
  font-weight: 600;
}

.preview-content :deep(blockquote) {
  border-left: 4px solid var(--primary);
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  background: var(--primary-light);
  border-radius: 0 var(--radius) var(--radius) 0;
}

/* History Panel */
.history-panel {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 320px;
  background: white;
  border-left: 1px solid var(--gray-200);
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--gray-200);
}

.history-header h3 {
  margin: 0;
  font-size: 1rem;
}

.close-btn {
  width: 28px;
  height: 28px;
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

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.history-item {
  padding: 0.75rem;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  margin-bottom: 0.5rem;
}

.history-item.major {
  border-color: var(--primary);
  background: var(--primary-light);
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.5rem;
}

.version-name {
  font-weight: 600;
  color: var(--gray-800);
}

.version-date {
  font-size: 0.75rem;
  color: var(--gray-500);
}

.version-summary {
  font-size: 0.8125rem;
  color: var(--gray-600);
}

.history-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  border: 1px solid var(--gray-300);
  background: white;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.btn-sm:hover {
  background: var(--gray-100);
}

.btn-sm.primary {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.no-history {
  text-align: center;
  padding: 2rem;
  color: var(--gray-500);
}

/* Modal */
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
  padding: 1.5rem;
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-dialog.large {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.modal-header h3 {
  margin: 0;
}

.modal-body {
  max-height: 60vh;
  overflow-y: auto;
  margin: 1rem 0;
  padding: 1rem;
  background: var(--gray-50);
  border-radius: var(--radius);
}

.modal-dialog h3 {
  margin-bottom: 1rem;
  color: var(--gray-800);
}

.form-group {
  margin-bottom: 1rem;
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

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.btn {
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius);
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn.secondary {
  background: white;
  border: 1px solid var(--gray-300);
  color: var(--gray-700);
}

.btn.secondary:hover {
  background: var(--gray-100);
}

.btn.primary {
  background: var(--primary);
  border: 1px solid var(--primary);
  color: white;
}

.btn.primary:hover {
  background: var(--primary-dark);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Section Menu */
.section-menu {
  position: fixed;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 50;
  min-width: 200px;
}

.section-menu-header {
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  color: var(--gray-500);
  text-transform: uppercase;
  border-bottom: 1px solid var(--gray-100);
}

.section-menu-item {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font-size: 0.875rem;
}

.section-menu-item:hover {
  background: var(--gray-100);
}

@media (max-width: 768px) {
  .editor-container.split {
    flex-direction: column;
  }

  .editor-container.split .edit-panel,
  .editor-container.split .preview-panel {
    width: 100%;
    height: 50%;
  }

  .edit-panel {
    border-right: none;
    border-bottom: 1px solid var(--gray-200);
  }

  .history-panel {
    width: 100%;
  }

  .toolbar-center {
    display: none;
  }
}
</style>
