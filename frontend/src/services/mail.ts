/**
 * Mail management service for managing accounts, quotas, aliases, and groups.
 */
import { authService } from './auth'

// ============================================================================
// Interfaces
// ============================================================================

export interface MailAccount {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  is_admin: boolean
  status: string
  created_at: string
  alias_count?: number
  group_count?: number
  quota?: string
}

export interface MailQuota {
  id: number
  user_id: number
  user_email: string
  size_value: number
  suffix: string
  quota_string: string
}

export interface MailAlias {
  id: number
  alias_email: string
  destination_email: string
  created_at: string | null
  user_id?: number
  user_email?: string
}

export interface MailGroup {
  id: number
  name: string
  description: string
  member_count: number
  updated_at: string | null
  created_at?: string | null
}

// ============================================================================
// Response Interfaces
// ============================================================================

interface BaseResponse {
  success: boolean
  error?: string
}

interface ListAccountsResponse extends BaseResponse {
  accounts: MailAccount[]
}

interface ListQuotasResponse extends BaseResponse {
  quotas: MailQuota[]
}

interface ListAliasesResponse extends BaseResponse {
  aliases: MailAlias[]
}

interface ListGroupsResponse extends BaseResponse {
  groups: MailGroup[]
}

interface CreateAccountResponse extends BaseResponse {
  account?: MailAccount
  message?: string
}

interface UpdateAccountResponse extends BaseResponse {
  message?: string
}

interface DeleteAccountResponse extends BaseResponse {
  message?: string
}

interface AccountGroupsResponse extends BaseResponse {
  account_id: number
  account_email?: string
  groups: { id: number; name: string }[]
}

interface CreateQuotaResponse extends BaseResponse {
  quota?: MailQuota
  message?: string
}

interface CreateAliasResponse extends BaseResponse {
  alias?: MailAlias
  message?: string
}

interface DeleteAliasResponse extends BaseResponse {
  message?: string
}

interface CreateGroupResponse extends BaseResponse {
  group?: MailGroup
  message?: string
}

interface UpdateGroupResponse extends BaseResponse {
  message?: string
}

interface DeleteGroupResponse extends BaseResponse {
  message?: string
}

interface GetGroupResponse extends BaseResponse {
  group?: {
    id: number
    name: string
    members: {
      id: number
      email: string
      username: string
      first_name: string
      last_name: string
    }[]
  }
}

// ============================================================================
// Mail Service
// ============================================================================

class MailService {
  /**
   * Get CSRF token from auth service
   */
  private getCSRFToken(): string {
    return authService.getCSRFTokenPublic()
  }

  // ==========================================================================
  // Mail Accounts
  // ==========================================================================

  /**
   * List all mail accounts (admin only)
   */
  async listAccounts(): Promise<ListAccountsResponse> {
    try {
      const response = await fetch('/api/mail/accounts/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to list accounts:', error)
      return {
        success: false,
        accounts: [],
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Create a new mail account (admin only)
   */
  async createAccount(accountData: {
    email: string
    username: string
    password: string
    first_name?: string
    last_name?: string
    is_admin?: boolean
  }): Promise<CreateAccountResponse> {
    try {
      const response = await fetch('/api/mail/accounts/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify(accountData),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to create account:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Update a mail account (admin only)
   */
  async updateAccount(
    accountId: number,
    updates: Partial<MailAccount>
  ): Promise<UpdateAccountResponse> {
    try {
      const response = await fetch(`/api/mail/accounts/${accountId}/update/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify(updates),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to update account:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Delete a mail account (admin only)
   */
  async deleteAccount(accountId: number): Promise<DeleteAccountResponse> {
    try {
      const response = await fetch(`/api/mail/accounts/${accountId}/delete/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to delete account:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Reset password for an account (admin only, non-admin targets)
   */
  async resetAccountPassword(accountId: number, password: string): Promise<BaseResponse> {
    try {
      const response = await fetch(`/api/mail/accounts/${accountId}/password/reset/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({ password }),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to reset password:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Get groups for an account
   */
  async getAccountGroups(accountId: number): Promise<AccountGroupsResponse> {
    try {
      const response = await fetch(`/api/mail/accounts/${accountId}/groups/`, {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to get account groups:', error)
      return {
        success: false,
        groups: [],
        error: 'Network error. Please try again.',
        account_id: accountId,
      }
    }
  }

  /**
   * Update groups for an account
   */
  async updateAccountGroups(accountId: number, groupIds: number[]): Promise<BaseResponse> {
    try {
      const response = await fetch(`/api/mail/accounts/${accountId}/groups/update/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          group_ids: groupIds,
        }),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to update account groups:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  // ==========================================================================
  // Mail Quotas
  // ==========================================================================

  /**
   * List all quotas (admin only)
   */
  async listQuotas(): Promise<ListQuotasResponse> {
    try {
      const response = await fetch('/api/mail/quotas/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to list quotas:', error)
      return {
        success: false,
        quotas: [],
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Create or update a quota (admin only)
   */
  async createOrUpdateQuota(
    userId: number,
    sizeValue: number,
    suffix: string = 'G'
  ): Promise<CreateQuotaResponse> {
    try {
      const response = await fetch('/api/mail/quotas/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          user_id: userId,
          size_value: sizeValue,
          suffix: suffix,
        }),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to create/update quota:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  // ==========================================================================
  // Mail Aliases
  // ==========================================================================

  /**
   * List all aliases (admin only)
   */
  async listAliases(): Promise<ListAliasesResponse> {
    try {
      const response = await fetch('/api/mail/aliases/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to list aliases:', error)
      return {
        success: false,
        aliases: [],
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Create a new alias (admin only)
   */
  async createAlias(
    aliasEmail: string,
    destinationEmail: string
  ): Promise<CreateAliasResponse> {
    try {
      const response = await fetch('/api/mail/aliases/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          alias_email: aliasEmail,
          destination_email: destinationEmail,
        }),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to create alias:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Delete an alias (admin only)
   */
  async deleteAlias(aliasId: number): Promise<DeleteAliasResponse> {
    try {
      const response = await fetch(`/api/mail/aliases/${aliasId}/delete/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
      })
      const text = await response.text()
      try {
        const data = JSON.parse(text)
        return data
      } catch {
        return {
          success: response.ok,
          error: text || 'Unexpected response from server',
        }
      }
    } catch (error) {
      console.error('Failed to delete alias:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  // ==========================================================================
  // Mail Groups
  // ==========================================================================

  /**
   * List all groups (admin only)
   */
  async listGroups(): Promise<ListGroupsResponse> {
    try {
      const response = await fetch('/api/mail/groups/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to list groups:', error)
      return {
        success: false,
        groups: [],
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Create a new group (admin only)
   */
  async createGroup(name: string, description: string = ''): Promise<CreateGroupResponse> {
    try {
      const response = await fetch('/api/mail/groups/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          name,
          description,
        }),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to create group:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Update a group (admin only)
   */
  async updateGroup(
    groupId: number,
    name?: string,
    description?: string
  ): Promise<UpdateGroupResponse> {
    try {
      const response = await fetch(`/api/mail/groups/${groupId}/update/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify({
          name,
          description,
        }),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to update group:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Delete a group (admin only)
   */
  async deleteGroup(groupId: number): Promise<DeleteGroupResponse> {
    try {
      const response = await fetch(`/api/mail/groups/${groupId}/delete/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to delete group:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }

  /**
   * Get a single group with members (admin only)
   */
  async getGroup(groupId: number): Promise<GetGroupResponse> {
    try {
      const response = await fetch(`/api/mail/groups/${groupId}/`, {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to get group:', error)
      return {
        success: false,
        error: 'Network error. Please try again.',
      }
    }
  }
}

export const mailService = new MailService()
