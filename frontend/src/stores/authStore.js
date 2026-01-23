/**
 * Auth Store
 *
 * Pinia store for managing Firebase authentication state
 */

import { defineStore } from 'pinia'
import { firebaseAuth } from '../services/firebase'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    loading: true,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    userId: (state) => state.user?.uid || null,
    userEmail: (state) => state.user?.email || null,
    userDisplayName: (state) =>
      state.user?.displayName ||
      state.user?.email?.split('@')[0] ||
      'User'
  },

  actions: {
    /**
     * Initialize auth state listener
     * Should be called once when app mounts
     * @returns {Promise<User|null>}
     */
    async initialize() {
      this.loading = true
      return new Promise((resolve) => {
        firebaseAuth.onAuthStateChanged((user) => {
          this.user = user
          this.loading = false
          resolve(user)
        })
      })
    },

    /**
     * Sign up with email and password
     * @param {string} email
     * @param {string} password
     * @returns {Promise<User>}
     */
    async signUpWithEmail(email, password) {
      this.loading = true
      this.error = null
      try {
        const result = await firebaseAuth.signUpWithEmail(email, password)
        this.user = result.user
        return result.user
      } catch (error) {
        this.error = this.getErrorMessage(error.code)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Sign in with email and password
     * @param {string} email
     * @param {string} password
     * @returns {Promise<User>}
     */
    async signInWithEmail(email, password) {
      this.loading = true
      this.error = null
      try {
        const result = await firebaseAuth.signInWithEmail(email, password)
        this.user = result.user
        return result.user
      } catch (error) {
        this.error = this.getErrorMessage(error.code)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Sign in with Google OAuth
     * @returns {Promise<User>}
     */
    async signInWithGoogle() {
      this.loading = true
      this.error = null
      try {
        const result = await firebaseAuth.signInWithGoogle()
        this.user = result.user
        return result.user
      } catch (error) {
        this.error = this.getErrorMessage(error.code)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Sign out current user
     */
    async signOut() {
      try {
        await firebaseAuth.signOut()
        this.user = null
        this.error = null
      } catch (error) {
        this.error = this.getErrorMessage(error.code)
        throw error
      }
    },

    /**
     * Get Firebase ID token for API calls
     * @returns {Promise<string|null>}
     */
    async getIdToken() {
      return firebaseAuth.getIdToken()
    },

    /**
     * Clear error message
     */
    clearError() {
      this.error = null
    },

    /**
     * Convert Firebase error codes to user-friendly messages
     * @param {string} errorCode
     * @returns {string}
     */
    getErrorMessage(errorCode) {
      const errorMessages = {
        'auth/email-already-in-use': 'This email is already registered. Please sign in instead.',
        'auth/invalid-email': 'Please enter a valid email address.',
        'auth/operation-not-allowed': 'This sign-in method is not enabled.',
        'auth/weak-password': 'Password is too weak. Please use at least 6 characters.',
        'auth/user-disabled': 'This account has been disabled. Please contact support.',
        'auth/user-not-found': 'No account found with this email. Please sign up first.',
        'auth/wrong-password': 'Incorrect password. Please try again.',
        'auth/invalid-credential': 'Invalid email or password. Please try again.',
        'auth/popup-closed-by-user': 'Sign-in was cancelled. Please try again.',
        'auth/cancelled-popup-request': 'Sign-in was cancelled.',
        'auth/popup-blocked': 'Popup was blocked. Please allow popups for this site.',
        'auth/network-request-failed': 'Network error. Please check your connection.',
        'auth/too-many-requests': 'Too many failed attempts. Please try again later.',
        'auth/requires-recent-login': 'Please sign in again to continue.'
      }
      return errorMessages[errorCode] || 'An error occurred. Please try again.'
    }
  }
})
