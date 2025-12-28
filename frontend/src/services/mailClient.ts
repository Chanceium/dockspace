/**
 * Mail Client Service
 * Handles API calls for IMAP/SMTP mail client functionality
 */

import { authService } from './auth'

export interface Mailbox {
  id: number
  name: string
  email: string
  imapHost: string
  imapPort: number
  imapSecurity: 'None' | 'SSL/TLS' | 'STARTTLS'
  smtpHost: string
  smtpPort: number
  smtpSecurity: 'None' | 'SSL/TLS' | 'STARTTLS'
  username: string
  password?: string
  color: string
  isActive: boolean
  hasError: boolean
  errorMessage?: string
  lastSync?: string
}

export interface Folder {
  name: string
  value: string
  icon: string
  count: number
}

export interface Email {
  id: number | string
  uid: string
  from: string
  fromEmail: string
  subject: string
  preview: string
  date: string
  time: string
  read: boolean
  starred: boolean
  hasAttachments?: boolean
}

export interface EmailDetail extends Email {
  to: string
  cc?: string
  body: string
  bodyHtml?: string
  attachments?: Array<{ name: string; size: number }>
}

export interface SendEmailRequest {
  to: string
  subject: string
  body: string
  cc?: string
  bcc?: string
  replyTo?: string
}

class MailClientService {
  private baseUrl = '/api/mailboxes'

  private async request<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<{ success: boolean; data?: T; error?: string }> {
    try {
      const csrfToken = authService.getCSRFTokenPublic()

      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
          ...options.headers,
        },
        credentials: 'include',
      })

      // Check if response is JSON
      const contentType = response.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        // Not JSON - likely redirected to login page
        if (response.status === 401) {
          return {
            success: false,
            error: 'Authentication required. Please log in.',
          }
        }
        return {
          success: false,
          error: 'Invalid response from server',
        }
      }

      const data = await response.json()

      if (!response.ok) {
        return {
          success: false,
          error: data.error || 'Request failed',
        }
      }

      return {
        success: true,
        data: data,
      }
    }
    catch (error) {
      console.error('Mail client request error:', error)
      return {
        success: false,
        error: 'Network error',
      }
    }
  }

  /**
   * List all mailboxes for current user
   */
  async listMailboxes(): Promise<{ success: boolean; mailboxes?: Mailbox[]; error?: string }> {
    const result = await this.request<{ mailboxes: Mailbox[] }>(this.baseUrl)

    if (result.success && result.data) {
      return {
        success: true,
        mailboxes: result.data.mailboxes,
      }
    }

    return {
      success: false,
      error: result.error,
    }
  }

  /**
   * Create a new mailbox configuration
   */
  async createMailbox(mailbox: Omit<Mailbox, 'id' | 'hasError' | 'errorMessage' | 'lastSync'>): Promise<{
    success: boolean
    mailbox?: Mailbox
    connectionTest?: { success: boolean; message: string }
    error?: string
  }> {
    const result = await this.request<{
      mailbox: Mailbox
      connectionTest: { success: boolean; message: string }
    }>(`${this.baseUrl}/create/`, {
      method: 'POST',
      body: JSON.stringify(mailbox),
    })

    if (result.success && result.data) {
      return {
        success: true,
        mailbox: result.data.mailbox,
        connectionTest: result.data.connectionTest,
      }
    }

    return {
      success: false,
      error: result.error,
    }
  }

  /**
   * Update mailbox configuration
   */
  async updateMailbox(
    mailboxId: number,
    updates: Partial<Mailbox>
  ): Promise<{
    success: boolean
    mailbox?: Mailbox
    connectionTest?: { success: boolean; message: string }
    error?: string
  }> {
    const result = await this.request<{
      mailbox: Mailbox
      connectionTest: { success: boolean; message: string }
    }>(`${this.baseUrl}/${mailboxId}/update/`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })

    if (result.success && result.data) {
      return {
        success: true,
        mailbox: result.data.mailbox,
        connectionTest: result.data.connectionTest,
      }
    }

    return {
      success: false,
      error: result.error,
    }
  }

  /**
   * Delete a mailbox
   */
  async deleteMailbox(mailboxId: number): Promise<{ success: boolean; error?: string }> {
    const result = await this.request(`${this.baseUrl}/${mailboxId}/delete/`, {
      method: 'DELETE',
    })

    return {
      success: result.success,
      error: result.error,
    }
  }

  /**
   * Test mailbox connection
   */
  async testConnection(mailboxId: number): Promise<{
    success: boolean
    connectionTest?: { success: boolean; message: string }
    error?: string
  }> {
    const result = await this.request<{
      connectionTest: { success: boolean; message: string }
    }>(`${this.baseUrl}/${mailboxId}/test/`, {
      method: 'POST',
    })

    if (result.success && result.data) {
      return {
        success: true,
        connectionTest: result.data.connectionTest,
      }
    }

    return {
      success: false,
      error: result.error,
    }
  }

  /**
   * List folders for a mailbox
   */
  async listFolders(mailboxId: number): Promise<{
    success: boolean
    folders?: Folder[]
    error?: string
  }> {
    const result = await this.request<{ folders: Folder[] }>(
      `${this.baseUrl}/${mailboxId}/folders/`
    )

    if (result.success && result.data) {
      return {
        success: true,
        folders: result.data.folders,
      }
    }

    return {
      success: false,
      error: result.error,
    }
  }

  /**
   * Fetch emails from a folder
   */
  async fetchEmails(
    mailboxId: number,
    folder: string = 'INBOX',
    limit: number = 50,
    offset: number = 0
  ): Promise<{ success: boolean; emails?: Email[]; count?: number; error?: string }> {
    const params = new URLSearchParams({
      folder,
      limit: limit.toString(),
      offset: offset.toString(),
    })

    const result = await this.request<{ emails: Email[]; count: number }>(
      `${this.baseUrl}/${mailboxId}/emails/?${params}`
    )

    if (result.success && result.data) {
      return {
        success: true,
        emails: result.data.emails,
        count: result.data.count,
      }
    }

    return {
      success: false,
      error: result.error,
    }
  }

  /**
   * Fetch full email details
   */
  async fetchEmailDetail(
    mailboxId: number,
    emailId: string,
    folder: string = 'INBOX'
  ): Promise<{ success: boolean; email?: EmailDetail; error?: string }> {
    const params = new URLSearchParams({ folder })

    const result = await this.request<{ email: EmailDetail }>(
      `${this.baseUrl}/${mailboxId}/emails/${emailId}/?${params}`
    )

    if (result.success && result.data) {
      return {
        success: true,
        email: result.data.email,
      }
    }

    return {
      success: false,
      error: result.error,
    }
  }

  /**
   * Send an email
   */
  async sendEmail(
    mailboxId: number,
    emailData: SendEmailRequest
  ): Promise<{ success: boolean; error?: string }> {
    const result = await this.request(`${this.baseUrl}/${mailboxId}/send/`, {
      method: 'POST',
      body: JSON.stringify(emailData),
    })

    return {
      success: result.success,
      error: result.error,
    }
  }
}

export const mailClientService = new MailClientService()
