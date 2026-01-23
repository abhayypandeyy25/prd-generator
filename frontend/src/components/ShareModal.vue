<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-dialog">
      <div class="modal-header">
        <h3>Share PRD</h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <!-- Create Share Link -->
        <div v-if="!shareLink" class="share-form">
          <div class="form-group">
            <label>Access Level</label>
            <div class="access-options">
              <label class="access-option" :class="{ selected: accessType === 'view' }">
                <input type="radio" v-model="accessType" value="view" />
                <div class="option-content">
                  <span class="option-icon">👁️</span>
                  <span class="option-title">View Only</span>
                  <span class="option-desc">Can only read the PRD</span>
                </div>
              </label>
              <label class="access-option" :class="{ selected: accessType === 'comment' }">
                <input type="radio" v-model="accessType" value="comment" />
                <div class="option-content">
                  <span class="option-icon">💬</span>
                  <span class="option-title">View & Comment</span>
                  <span class="option-desc">Can add comments and feedback</span>
                </div>
              </label>
              <label class="access-option" :class="{ selected: accessType === 'edit' }">
                <input type="radio" v-model="accessType" value="edit" />
                <div class="option-content">
                  <span class="option-icon">✏️</span>
                  <span class="option-title">Full Edit</span>
                  <span class="option-desc">Can edit the PRD content</span>
                </div>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>Link Expiration</label>
            <select v-model="expiresIn" class="form-select">
              <option :value="1">1 day</option>
              <option :value="7">7 days</option>
              <option :value="30">30 days</option>
              <option :value="null">Never expires</option>
            </select>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="usePassword" />
              Require password
            </label>
            <input
              v-if="usePassword"
              v-model="password"
              type="password"
              placeholder="Enter password"
              class="form-input"
              style="margin-top: 0.5rem;"
            />
          </div>

          <button
            class="btn btn-primary full-width"
            @click="createShareLink"
            :disabled="isCreating"
          >
            {{ isCreating ? 'Creating...' : 'Create Share Link' }}
          </button>
        </div>

        <!-- Share Link Created -->
        <div v-else class="share-success">
          <div class="success-icon">✅</div>
          <h4>Link Created!</h4>

          <div class="share-link-box">
            <input
              ref="linkInput"
              type="text"
              :value="shareLink"
              readonly
              class="share-link-input"
            />
            <button class="copy-btn" @click="copyLink" :class="{ copied }">
              {{ copied ? '✓ Copied' : '📋 Copy' }}
            </button>
          </div>

          <div class="share-details">
            <span class="detail">
              <span class="detail-label">Access:</span>
              {{ accessTypeLabel }}
            </span>
            <span class="detail">
              <span class="detail-label">Expires:</span>
              {{ expiresLabel }}
            </span>
            <span v-if="usePassword" class="detail">
              <span class="detail-label">Password protected</span>
            </span>
          </div>

          <button class="btn btn-secondary" @click="resetForm">
            Create Another Link
          </button>
        </div>

        <!-- Existing Share Links -->
        <div v-if="existingShares.length > 0" class="existing-shares">
          <h4>Active Share Links</h4>
          <div class="shares-list">
            <div v-for="share in existingShares" :key="share.id" class="share-item">
              <div class="share-info">
                <span class="share-access">{{ getAccessLabel(share.access_type) }}</span>
                <span class="share-views">{{ share.view_count }} views</span>
                <span v-if="share.expires_at" class="share-expires">
                  Expires {{ formatDate(share.expires_at) }}
                </span>
              </div>
              <button class="btn-icon" @click="revokeShare(share.id)" title="Revoke">
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { shareApi } from '../services/api'
import { useProjectStore } from '../stores/projectStore'

const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const store = useProjectStore()

const accessType = ref('view')
const expiresIn = ref(7)
const usePassword = ref(false)
const password = ref('')
const isCreating = ref(false)
const shareLink = ref('')
const shareToken = ref('')
const copied = ref(false)
const existingShares = ref([])
const linkInput = ref(null)

const accessTypeLabel = computed(() => {
  const labels = {
    view: 'View Only',
    comment: 'View & Comment',
    edit: 'Full Edit'
  }
  return labels[accessType.value] || 'View Only'
})

const expiresLabel = computed(() => {
  if (!expiresIn.value) return 'Never'
  return `${expiresIn.value} day${expiresIn.value > 1 ? 's' : ''}`
})

const getAccessLabel = (type) => {
  const labels = {
    view: '👁️ View',
    comment: '💬 Comment',
    edit: '✏️ Edit'
  }
  return labels[type] || type
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const fetchExistingShares = async () => {
  try {
    const response = await shareApi.list(props.projectId)
    existingShares.value = response.data?.shares || []
  } catch (error) {
    console.error('Failed to fetch shares:', error)
  }
}

const createShareLink = async () => {
  isCreating.value = true

  try {
    const options = {
      access_type: accessType.value,
      expires_in: expiresIn.value,
      password: usePassword.value ? password.value : null
    }

    const response = await shareApi.create(props.projectId, options)

    if (response.data?.share_token) {
      shareToken.value = response.data.share_token
      shareLink.value = `${window.location.origin}/shared/${response.data.share_token}`
      await fetchExistingShares()
    }
  } catch (error) {
    console.error('Failed to create share link:', error)
    store.showToast('Failed to create share link', 'error')
  } finally {
    isCreating.value = false
  }
}

const copyLink = async () => {
  try {
    await navigator.clipboard.writeText(shareLink.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (error) {
    // Fallback for older browsers
    linkInput.value?.select()
    document.execCommand('copy')
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

const revokeShare = async (shareId) => {
  try {
    await shareApi.revoke(shareId)
    existingShares.value = existingShares.value.filter(s => s.id !== shareId)
    store.showToast('Share link revoked', 'success')
  } catch (error) {
    console.error('Failed to revoke share:', error)
    store.showToast('Failed to revoke share link', 'error')
  }
}

const resetForm = () => {
  shareLink.value = ''
  shareToken.value = ''
  password.value = ''
  usePassword.value = false
}

onMounted(() => {
  fetchExistingShares()
})
</script>

<style scoped>
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

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--gray-700);
}

.access-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.access-option {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.15s ease;
}

.access-option:hover {
  border-color: var(--gray-300);
}

.access-option.selected {
  border-color: var(--primary);
  background: var(--primary-light);
}

.access-option input {
  display: none;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.option-icon {
  font-size: 1.25rem;
}

.option-title {
  font-weight: 500;
  color: var(--gray-800);
}

.option-desc {
  font-size: 0.8125rem;
  color: var(--gray-500);
}

.form-select,
.form-input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 0.9375rem;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.btn {
  padding: 0.75rem 1.25rem;
  border-radius: var(--radius);
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-primary {
  background: var(--primary);
  border: 1px solid var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: white;
  border: 1px solid var(--gray-300);
  color: var(--gray-700);
}

.btn-secondary:hover {
  background: var(--gray-100);
}

.full-width {
  width: 100%;
}

/* Share Success */
.share-success {
  text-align: center;
}

.success-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.share-success h4 {
  margin: 0 0 1.5rem;
  color: var(--gray-800);
}

.share-link-box {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.share-link-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  background: var(--gray-50);
  font-size: 0.875rem;
  color: var(--gray-700);
}

.copy-btn {
  padding: 0.75rem 1rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.copy-btn.copied {
  background: var(--success);
}

.share-details {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
}

.detail-label {
  color: var(--gray-500);
  margin-right: 0.25rem;
}

/* Existing Shares */
.existing-shares {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--gray-200);
}

.existing-shares h4 {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  color: var(--gray-600);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.shares-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.share-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: var(--gray-50);
  border-radius: var(--radius);
}

.share-info {
  display: flex;
  gap: 1rem;
  font-size: 0.8125rem;
}

.share-access {
  font-weight: 500;
  color: var(--gray-700);
}

.share-views,
.share-expires {
  color: var(--gray-500);
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: var(--radius);
  transition: background 0.15s ease;
}

.btn-icon:hover {
  background: var(--gray-200);
}

@media (max-width: 480px) {
  .option-desc {
    display: none;
  }

  .share-details {
    flex-direction: column;
    gap: 0.5rem;
  }

  .share-info {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>
