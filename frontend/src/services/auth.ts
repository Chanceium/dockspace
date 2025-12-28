/**
 * Authentication service for Vue3 frontend.
 * Uses Django's session-based authentication with CSRF protection.
 */

interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  is_admin: boolean
  picture?: string | null
}

interface LoginResponse {
  success: boolean
  user?: User
  message?: string
  error?: string
  requiresTOTP?: boolean
}

interface SessionResponse {
  authenticated: boolean
  user?: User
}

interface SetupCheckResponse {
  needsSetup: boolean
  userCount: number
}

class AuthService {
  /**
   * Initialize CSRF token on app startup
   */
  async initCSRF(): Promise<void> {
    try {
      // Fetch CSRF endpoint to ensure cookie is set
      await fetch('/api/csrf/', {
        credentials: 'include',
      })
    } catch (error) {
      console.error('Failed to initialize CSRF:', error)
    }
  }

  /**
   * Get CSRF token from cookie
   * Reads directly from cookie to avoid stale cached tokens
   */
  private getCSRFToken(): string {
    const name = 'csrftoken'
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) {
      return parts.pop()?.split(';').shift() || ''
    }
    return ''
  }

  /**
   * Public method to get CSRF token for external use
   */
  getCSRFTokenPublic(): string {
    return this.getCSRFToken()
  }

  /**
   * Login with email and password
   */
  async login(email: string, password: string, otpToken?: string): Promise<LoginResponse> {
    try {
      const response = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          email,
          password,
          otp_token: otpToken
        }),
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Login error:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      await fetch('/api/auth/logout/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
      })
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  /**
   * Check if user is authenticated and get user data
   */
  async checkSession(): Promise<SessionResponse> {
    try {
      const response = await fetch('/api/auth/session/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Session check error:', error)
      return { authenticated: false }
    }
  }

  /**
   * Check if initial setup is needed
   */
  async checkSetup(): Promise<SetupCheckResponse> {
    try {
      const response = await fetch('/api/setup/check/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Setup check error:', error)
      return { needsSetup: false, userCount: 0 }
    }
  }

  /**
   * Register new user (only during initial setup)
   */
  async register(userData: {
    email: string
    password: string
    first_name: string
    last_name: string
    username?: string
  }): Promise<LoginResponse> {
    try {
      const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify(userData),
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Registration error:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Complete initial setup with admin account and app settings
   */
  async completeSetup(setupData: {
    email: string
    password: string
    first_name: string
    last_name: string
    session_timeout: number
    domain_url: string
  }): Promise<LoginResponse> {
    try {
      const response = await fetch('/api/setup/complete/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify(setupData),
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Setup error:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }
}

export const authService = new AuthService()
export type { User, LoginResponse, SessionResponse, SetupCheckResponse }
