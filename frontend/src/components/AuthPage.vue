<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="app-title">PM <span>Clarity</span></h1>
      <p class="auth-subtitle">Get complete clarity on your product idea</p>

      <!-- Error Message -->
      <div v-if="authStore.error" class="error-message">
        {{ authStore.error }}
      </div>

      <!-- Toggle between Login and Sign Up -->
      <div class="auth-tabs">
        <button
          :class="['auth-tab', { active: mode === 'login' }]"
          @click="switchMode('login')"
        >
          Login
        </button>
        <button
          :class="['auth-tab', { active: mode === 'signup' }]"
          @click="switchMode('signup')"
        >
          Sign Up
        </button>
      </div>

      <!-- Email Form -->
      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="you@example.com"
            required
            :disabled="isLoading"
          />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            :placeholder="mode === 'signup' ? 'Min 6 characters' : 'Enter your password'"
            minlength="6"
            required
            :disabled="isLoading"
          />
        </div>
        <button
          type="submit"
          class="btn btn-primary btn-full"
          :disabled="isLoading"
        >
          <span v-if="isLoading" class="btn-loading"></span>
          {{ mode === 'login' ? 'Sign In' : 'Create Account' }}
        </button>
      </form>

      <div class="auth-divider">
        <span>or</span>
      </div>

      <!-- Google Sign In -->
      <button
        @click="handleGoogleSignIn"
        class="btn btn-google btn-full"
        :disabled="isLoading"
      >
        <svg class="google-icon" viewBox="0 0 24 24" width="20" height="20">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Continue with Google
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/authStore'

const authStore = useAuthStore()

const mode = ref('login')
const email = ref('')
const password = ref('')
const isLoading = computed(() => authStore.loading)

const switchMode = (newMode) => {
  mode.value = newMode
  authStore.clearError()
}

const handleSubmit = async () => {
  authStore.clearError()
  try {
    if (mode.value === 'login') {
      await authStore.signInWithEmail(email.value, password.value)
    } else {
      await authStore.signUpWithEmail(email.value, password.value)
    }
    // Clear form on success
    email.value = ''
    password.value = ''
  } catch (error) {
    console.error('Auth error:', error)
  }
}

const handleGoogleSignIn = async () => {
  authStore.clearError()
  try {
    await authStore.signInWithGoogle()
  } catch (error) {
    console.error('Google sign-in error:', error)
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--gray-50) 0%, var(--gray-100) 100%);
  padding: 1rem;
}

.auth-card {
  background: white;
  padding: 2.5rem;
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.app-title {
  font-size: 2rem;
  font-weight: 700;
  text-align: center;
  margin: 0 0 0.5rem 0;
  color: var(--gray-900);
}

.app-title span {
  color: var(--primary);
}

.auth-subtitle {
  color: var(--gray-500);
  text-align: center;
  margin-bottom: 2rem;
  font-size: 0.9375rem;
}

.error-message {
  background: var(--red-50, #fef2f2);
  color: var(--red-600, #dc2626);
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  margin-bottom: 1rem;
  font-size: 0.875rem;
  border: 1px solid var(--red-200, #fecaca);
}

.auth-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--gray-200);
}

.auth-tab {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--gray-500);
  font-weight: 500;
  font-size: 0.9375rem;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.auth-tab:hover {
  color: var(--gray-700);
}

.auth-tab.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--gray-700);
}

.form-group input {
  padding: 0.75rem 1rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input:disabled {
  background: var(--gray-100);
  cursor: not-allowed;
}

.btn-full {
  width: 100%;
  padding: 0.875rem 1rem;
  font-size: 1rem;
}

.btn-loading {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
  margin-right: 0.5rem;
  vertical-align: middle;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.auth-divider {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
  color: var(--gray-400);
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--gray-200);
}

.auth-divider span {
  padding: 0 1rem;
  font-size: 0.875rem;
}

.btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  background: white;
  border: 1px solid var(--gray-300);
  color: var(--gray-700);
  font-weight: 500;
}

.btn-google:hover:not(:disabled) {
  background: var(--gray-50);
  border-color: var(--gray-400);
}

.btn-google:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.google-icon {
  flex-shrink: 0;
}

@media (max-width: 480px) {
  .auth-card {
    padding: 1.5rem;
    margin: 0.5rem;
  }

  .app-title {
    font-size: 1.75rem;
  }
}
</style>
