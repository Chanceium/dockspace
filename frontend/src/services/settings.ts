/**
 * Application settings service for admin-only configuration.
 */
import { authService } from './auth'

export interface AppSettings {
  session_timeout: number
  domain_url: string
  allow_registration: boolean
  smtp_host: string
  smtp_port: number
  smtp_username: string
  smtp_password?: string
  smtp_from_email: string
  smtp_security: 'none' | 'starttls' | 'ssl'
}

interface BaseResponse {
  success: boolean
  error?: string
  message?: string
}

interface GetSettingsResponse extends BaseResponse {
  settings?: AppSettings
}

class SettingsService {
  private getCSRFToken(): string {
    return authService.getCSRFTokenPublic()
  }

  async getSettings(): Promise<GetSettingsResponse> {
    try {
      const response = await fetch('/api/settings/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to get settings:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  async updateSettings(settings: Partial<AppSettings>): Promise<BaseResponse> {
    try {
      const response = await fetch('/api/settings/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify(settings),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to update settings:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }
}

export const settingsService = new SettingsService()
