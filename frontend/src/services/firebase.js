/**
 * Firebase Authentication Service
 *
 * Provides Firebase Auth initialization and authentication methods
 * for PM Clarity application.
 */

import { initializeApp } from 'firebase/app'
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged
} from 'firebase/auth'

// Firebase configuration from environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
}

// Initialize Firebase
const app = initializeApp(firebaseConfig)
export const auth = getAuth(app)
export const googleProvider = new GoogleAuthProvider()

// Configure Google provider
googleProvider.setCustomParameters({
  prompt: 'select_account'
})

/**
 * Firebase Authentication Methods
 */
export const firebaseAuth = {
  /**
   * Sign up with email and password
   * @param {string} email
   * @param {string} password
   * @returns {Promise<UserCredential>}
   */
  signUpWithEmail: (email, password) =>
    createUserWithEmailAndPassword(auth, email, password),

  /**
   * Sign in with email and password
   * @param {string} email
   * @param {string} password
   * @returns {Promise<UserCredential>}
   */
  signInWithEmail: (email, password) =>
    signInWithEmailAndPassword(auth, email, password),

  /**
   * Sign in with Google OAuth
   * @returns {Promise<UserCredential>}
   */
  signInWithGoogle: () =>
    signInWithPopup(auth, googleProvider),

  /**
   * Sign out current user
   * @returns {Promise<void>}
   */
  signOut: () => signOut(auth),

  /**
   * Get current user
   * @returns {User|null}
   */
  getCurrentUser: () => auth.currentUser,

  /**
   * Get ID token for API calls
   * @returns {Promise<string|null>}
   */
  getIdToken: async () => {
    const user = auth.currentUser
    if (user) {
      try {
        return await user.getIdToken()
      } catch (error) {
        console.error('Error getting ID token:', error)
        return null
      }
    }
    return null
  },

  /**
   * Subscribe to auth state changes
   * @param {function} callback - Called with user object or null
   * @returns {function} Unsubscribe function
   */
  onAuthStateChanged: (callback) => onAuthStateChanged(auth, callback)
}

export default firebaseAuth
