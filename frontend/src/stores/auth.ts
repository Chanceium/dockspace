/**
 * Pinia store for authentication state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService, type User } from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => user.value !== null)
  const isAdmin = computed(() => user.value?.is_admin ?? false)
  const isLoading = ref(false)
  const pendingLogin = ref<{ email: string; password: string } | null>(null)

  /**
   * Initialize auth state by checking session
   */
  async function init() {
    isLoading.value = true
    try {
      // Initialize CSRF token
      await authService.initCSRF()

      // Check if user is authenticated
      const session = await authService.checkSession()
      if (session.authenticated && session.user) {
        user.value = session.user
      } else {
        user.value = null
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error)
      user.value = null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Login user
   */
  async function login(email: string, password: string, otpToken?: string) {
    isLoading.value = true
    try {
      const response = await authService.login(email, password, otpToken)

      if (response.success && response.user) {
        user.value = response.user
        pendingLogin.value = null
        return { success: true }
      } else {
        if (response.requiresTOTP) {
          pendingLogin.value = { email, password }
        } else {
          pendingLogin.value = null
        }
        return {
          success: false,
          error: response.error || 'Login failed',
          requiresTOTP: response.requiresTOTP,
        }
      }
    } catch (error) {
      return {
        success: false,
        error: 'An error occurred during login'
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Logout user
   */
  async function logout() {
    isLoading.value = true
    try {
      await authService.logout()
      user.value = null
      pendingLogin.value = null
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register new user
   */
  async function register(userData: {
    email: string
    password: string
    first_name: string
    last_name: string
    username?: string
  }) {
    isLoading.value = true
    try {
      const response = await authService.register(userData)

      if (response.success && response.user) {
        user.value = response.user
        return { success: true }
      } else {
        return {
          success: false,
          error: response.error || 'Registration failed'
        }
      }
    } catch (error) {
      return {
        success: false,
        error: 'An error occurred during registration'
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Complete initial setup
   */
  async function completeSetup(setupData: {
    email: string
    password: string
    first_name: string
    last_name: string
    session_timeout: number
    domain_url: string
  }) {
    isLoading.value = true
    try {
      const response = await authService.completeSetup(setupData)

      if (response.success && response.user) {
        user.value = response.user
        return { success: true }
      } else {
        return {
          success: false,
          error: response.error || 'Setup failed'
        }
      }
    } catch (error) {
      return {
        success: false,
        error: 'An error occurred during setup'
      }
    } finally {
      isLoading.value = false
    }
  }

  return {
    user,
    isAuthenticated,
    isAdmin,
    isLoading,
    pendingLogin,
    init,
    login,
    logout,
    register,
    completeSetup
  }
})
