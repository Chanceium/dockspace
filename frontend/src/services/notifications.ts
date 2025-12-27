import { authService } from './auth'

export interface Notification {
  id: number
  action: string
  action_display: string
  description: string
  created_at: string
  severity: 'info' | 'warning' | 'critical'
  category: string
  is_personal: boolean
  is_admin_only: boolean
  actor: {
    id: number
    name: string
  } | null
}

export interface NotificationPreferences {
  [key: string]: {
    email: boolean
    browser: boolean
  }
}

interface GetNotificationsResponse {
  success: boolean
  notifications?: Notification[]
  unread_count?: number
  error?: string
}

interface GetUnreadCountResponse {
  success: boolean
  count?: number
  error?: string
}

interface GetPreferencesResponse {
  success: boolean
  preferences?: NotificationPreferences
  error?: string
}

interface UpdatePreferencesResponse {
  success: boolean
  message?: string
  error?: string
}

interface CheckSmtpStatusResponse {
  success: boolean
  smtp_configured?: boolean
  error?: string
}

class NotificationService {
  private getCSRFToken(): string {
    return authService.getCSRFTokenPublic()
  }

  async getNotifications(): Promise<GetNotificationsResponse> {
    try {
      const response = await fetch('/api/notifications/', {
        credentials: 'include',
      })

      const data = await response.json()
      return data
    }
    catch (error) {
      console.error('Failed to fetch notifications:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async getUnreadCount(): Promise<GetUnreadCountResponse> {
    try {
      const response = await fetch('/api/notifications/unread-count/', {
        credentials: 'include',
      })

      const data = await response.json()
      return data
    }
    catch (error) {
      console.error('Failed to fetch unread count:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async getPreferences(): Promise<GetPreferencesResponse> {
    try {
      const response = await fetch('/api/notifications/preferences/', {
        credentials: 'include',
      })

      const data = await response.json()
      return data
    }
    catch (error) {
      console.error('Failed to fetch notification preferences:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async updatePreferences(preferences: NotificationPreferences): Promise<UpdatePreferencesResponse> {
    try {
      const response = await fetch('/api/notifications/preferences/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({ preferences }),
      })

      const data = await response.json()
      return data
    }
    catch (error) {
      console.error('Failed to update notification preferences:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async checkSmtpStatus(): Promise<CheckSmtpStatusResponse> {
    try {
      const response = await fetch('/api/notifications/smtp-status/', {
        credentials: 'include',
      })

      const data = await response.json()
      return data
    }
    catch (error) {
      console.error('Failed to check SMTP status:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async dismissNotification(notificationId: number): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await fetch(`/api/notifications/${notificationId}/dismiss/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
      })

      const data = await response.json()
      return data
    }
    catch (error) {
      console.error('Failed to dismiss notification:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }
}

export const notificationService = new NotificationService()
