/**
 * Profile service for managing user profile and password operations.
 */
import { authService } from './auth'

interface PasswordRequirementsResponse {
  success: boolean
  requirements: string[]
}

interface ChangePasswordResponse {
  success: boolean
  message?: string
  error?: string
  errors?: string[]
}

interface TOTPDevice {
  id: number
  name: string
  verified_at: string | null
  last_used_at: string | null
  created_at: string
}

interface TOTPStatusResponse {
  success: boolean
  enabled: boolean
  device_count: number
}

interface ListDevicesResponse {
  success: boolean
  devices: TOTPDevice[]
  has_totp: boolean
  error?: string
}

interface CreateDeviceResponse {
  success: boolean
  device?: {
    id: number
    name: string
    secret: string
    provisioning_uri: string
  }
  message?: string
  error?: string
}

interface VerifyDeviceResponse {
  success: boolean
  message?: string
  error?: string
}

interface DeleteDeviceResponse {
  success: boolean
  message?: string
  error?: string
}

export interface UserSession {
  id: number
  browser: string
  device: string
  location: string
  ip_address: string
  last_activity: string
  created_at: string
  is_active: boolean
  is_current: boolean
}

interface ListSessionsResponse {
  success: boolean
  sessions: UserSession[]
  error?: string
}

class ProfileService {
  /**
   * Get CSRF token from auth service
   */
  private getCSRFToken(): string {
    return authService.getCSRFTokenPublic()
  }

  /**
   * Get password requirements from backend validators
   */
  async getPasswordRequirements(): Promise<PasswordRequirementsResponse> {
    try {
      const response = await fetch('/api/profile/password-requirements/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to fetch password requirements:', error)
      return {
        success: false,
        requirements: [],
      }
    }
  }

  /**
   * Change user password
   */
  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<ChangePasswordResponse> {
    try {
      const response = await fetch('/api/profile/change-password/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Password change error:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Get TOTP status
   */
  async getTOTPStatus(): Promise<TOTPStatusResponse> {
    try {
      const response = await fetch('/api/totp/status/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to get TOTP status:', error)
      return {
        success: false,
        enabled: false,
        device_count: 0,
      }
    }
  }

  /**
   * List all TOTP devices
   */
  async listTOTPDevices(): Promise<ListDevicesResponse> {
    try {
      const response = await fetch('/api/totp/devices/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to list TOTP devices:', error)
      return {
        success: false,
        devices: [],
        has_totp: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Create a new TOTP device
   */
  async createTOTPDevice(deviceName: string): Promise<CreateDeviceResponse> {
    try {
      const response = await fetch('/api/totp/devices/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          name: deviceName,
        }),
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to create TOTP device:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Verify a TOTP device with a token
   */
  async verifyTOTPDevice(
    deviceId: number,
    token: string
  ): Promise<VerifyDeviceResponse> {
    try {
      const response = await fetch('/api/totp/devices/verify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          device_id: deviceId,
          token: token,
        }),
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to verify TOTP device:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Delete a TOTP device
   */
  async deleteTOTPDevice(deviceId: number): Promise<DeleteDeviceResponse> {
    try {
      const response = await fetch(`/api/totp/devices/${deviceId}/delete/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to delete TOTP device:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * List recent login sessions
   */
  async listSessions(): Promise<ListSessionsResponse> {
    try {
      const response = await fetch('/api/sessions/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to list sessions:', error)
      return {
        success: false,
        sessions: [],
        error: 'Network error. Please try again.',
      }
    }
  }
}

export const profileService = new ProfileService()
export type {
  PasswordRequirementsResponse,
  ChangePasswordResponse,
  TOTPDevice,
  TOTPStatusResponse,
  ListDevicesResponse,
  CreateDeviceResponse,
  VerifyDeviceResponse,
  DeleteDeviceResponse,
  ListSessionsResponse,
}
