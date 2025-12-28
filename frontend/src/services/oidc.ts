import { authService } from './auth'

export type OIDCClientType = 'confidential' | 'public'
export type OIDCResponseType =
  | 'code'
  | 'id_token'
  | 'id_token token'
  | 'code token'
  | 'code id_token'
  | 'code id_token token'

export interface OIDCClient {
  id: number
  name: string
  client_id: string
  client_secret?: string
  client_type: OIDCClientType
  response_types: OIDCResponseType[]
  jwt_alg: string
  redirect_uris: string[]
  scope: string
  created_at?: string | null
  updated_at?: string | null
  group_count?: number
  require_2fa?: boolean
  groups?: { id: number; name: string }[]
}

interface BaseResponse {
  success: boolean
  error?: string
  message?: string
}

interface ListClientsResponse extends BaseResponse {
  clients?: OIDCClient[]
}

interface GetClientResponse extends BaseResponse {
  client?: OIDCClient
}

interface CreateClientResponse extends BaseResponse {
  client?: OIDCClient
}

class OIDCService {
  private getCSRFToken(): string {
    return authService.getCSRFTokenPublic()
  }

  async listClients(): Promise<ListClientsResponse> {
    try {
      const response = await fetch('/api/oidc/clients/', {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to list OIDC clients:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async getClient(id: number): Promise<GetClientResponse> {
    try {
      const response = await fetch(`/api/oidc/clients/${id}/`, {
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to get OIDC client:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async createClient(payload: Partial<OIDCClient> & { group_ids?: number[]; require_2fa?: boolean }): Promise<CreateClientResponse> {
    try {
      const response = await fetch('/api/oidc/clients/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to create OIDC client:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async updateClient(id: number, payload: Partial<OIDCClient> & { group_ids?: number[]; require_2fa?: boolean }): Promise<BaseResponse> {
    try {
      const response = await fetch(`/api/oidc/clients/${id}/update/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to update OIDC client:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async deleteClient(id: number): Promise<BaseResponse> {
    try {
      const response = await fetch(`/api/oidc/clients/${id}/delete/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': this.getCSRFToken(),
        },
        credentials: 'include',
      })
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to delete OIDC client:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }
}

export const oidcService = new OIDCService()
