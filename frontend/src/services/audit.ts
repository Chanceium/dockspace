import { authService } from './auth'

export interface AuditLog {
  id: number
  action: string
  action_display: string
  actor: {
    id: number
    email: string
    name: string
  } | null
  target_type: string
  target_id: number | null
  target_name: string
  description: string
  metadata: Record<string, any>
  ip_address: string | null
  severity: 'info' | 'warning' | 'critical'
  success: boolean
  created_at: string
}

export interface AuditPagination {
  page: number
  page_size: number
  total_pages: number
  total_count: number
  has_next: boolean
  has_previous: boolean
}

export interface AuditFilters {
  action_types: { value: string; label: string }[]
  severity_levels: { value: string; label: string }[]
}

interface ListAuditLogsParams {
  page?: number
  page_size?: number
  action?: string
  actor?: string
  severity?: string
  search?: string
  start_date?: string
  end_date?: string
}

interface ListAuditLogsResponse {
  success: boolean
  logs?: AuditLog[]
  pagination?: AuditPagination
  filters?: AuditFilters
  error?: string
}

interface AuditStatsResponse {
  success: boolean
  stats?: {
    total_logs: number
    last_24h: number
    last_7d: number
    last_30d: number
    critical_count: number
    failed_actions: number
    recent_critical: Array<{
      id: number
      action: string
      description: string
      created_at: string
    }>
    action_distribution: Array<{
      action: string
      count: number
    }>
  }
  error?: string
}

class AuditService {
  private getCSRFToken(): string {
    return authService.getCSRFTokenPublic()
  }

  async listAuditLogs(params: ListAuditLogsParams = {}): Promise<ListAuditLogsResponse> {
    try {
      const queryParams = new URLSearchParams()

      if (params.page) queryParams.append('page', params.page.toString())
      if (params.page_size) queryParams.append('page_size', params.page_size.toString())
      if (params.action) queryParams.append('action', params.action)
      if (params.actor) queryParams.append('actor', params.actor)
      if (params.severity) queryParams.append('severity', params.severity)
      if (params.search) queryParams.append('search', params.search)
      if (params.start_date) queryParams.append('start_date', params.start_date)
      if (params.end_date) queryParams.append('end_date', params.end_date)

      const url = `/api/audit/logs/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`

      const response = await fetch(url, {
        credentials: 'include',
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }

  async getStats(): Promise<AuditStatsResponse> {
    try {
      const response = await fetch('/api/audit/stats/', {
        credentials: 'include',
      })

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Failed to fetch audit stats:', error)
      return { success: false, error: 'Network error. Please try again.' }
    }
  }
}

export const auditService = new AuditService()
