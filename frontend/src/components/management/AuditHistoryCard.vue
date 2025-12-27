<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { auditService } from '@/services/audit'
import type { AuditLog, AuditFilters } from '@/services/audit'

const logs = ref<AuditLog[]>([])
const isLoading = ref(false)
const filters = ref<AuditFilters>({
  action_types: [],
  severity_levels: [],
})

// Filter state
const selectedAction = ref('')
const selectedSeverity = ref('')
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(25)
const totalPages = ref(1)
const totalCount = ref(0)

// Computed
const hasFilters = computed(() => {
  return selectedAction.value || selectedSeverity.value || searchQuery.value
})

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'error'
    case 'warning':
      return 'warning'
    default:
      return 'info'
  }
}

const getActionIcon = (action: string) => {
  if (action.startsWith('account.'))
    return 'ri-user-line'
  if (action.startsWith('alias.'))
    return 'ri-mail-line'
  if (action.startsWith('group.'))
    return 'ri-group-line'
  if (action.startsWith('oidc.'))
    return 'ri-shield-keyhole-line'
  if (action.startsWith('settings.'))
    return 'ri-settings-line'
  if (action.startsWith('auth.'))
    return 'ri-lock-line'
  if (action.startsWith('session.'))
    return 'ri-device-line'
  return 'ri-information-line'
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString()
}

const loadLogs = async () => {
  isLoading.value = true
  const response = await auditService.listAuditLogs({
    page: currentPage.value,
    page_size: pageSize.value,
    action: selectedAction.value,
    severity: selectedSeverity.value,
    search: searchQuery.value,
  })

  if (response.success && response.logs) {
    logs.value = response.logs
    if (response.pagination) {
      totalPages.value = response.pagination.total_pages
      totalCount.value = response.pagination.total_count
    }
    if (response.filters) {
      filters.value = response.filters
    }
  }
  isLoading.value = false
}

const clearFilters = () => {
  selectedAction.value = ''
  selectedSeverity.value = ''
  searchQuery.value = ''
  currentPage.value = 1
  loadLogs()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadLogs()
}

onMounted(() => {
  loadLogs()
})

defineExpose({
  loadLogs,
})
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle>Audit History</VCardTitle>
      <VCardSubtitle>Track all administrative actions and system events</VCardSubtitle>
    </VCardItem>

    <VDivider />

    <!-- Filters -->
    <VCardText>
      <VRow dense>
        <VCol cols="12" md="3">
          <VTextField
            v-model="searchQuery"
            label="Search"
            placeholder="Search description..."
            prepend-inner-icon="ri-search-line"
            clearable
            density="compact"
            @update:model-value="loadLogs"
          />
        </VCol>
        <VCol cols="12" md="3">
          <VSelect
            v-model="selectedAction"
            label="Action Type"
            :items="filters.action_types"
            item-title="label"
            item-value="value"
            clearable
            density="compact"
            @update:model-value="loadLogs"
          />
        </VCol>
        <VCol cols="12" md="3">
          <VSelect
            v-model="selectedSeverity"
            label="Severity"
            :items="filters.severity_levels"
            item-title="label"
            item-value="value"
            clearable
            density="compact"
            @update:model-value="loadLogs"
          />
        </VCol>
        <VCol cols="12" md="3" class="d-flex align-center">
          <VBtn
            v-if="hasFilters"
            variant="outlined"
            size="small"
            @click="clearFilters"
          >
            Clear Filters
          </VBtn>
          <VSpacer />
          <VBtn
            icon="ri-refresh-line"
            variant="text"
            size="small"
            @click="loadLogs"
          />
        </VCol>
      </VRow>
    </VCardText>

    <VDivider />

    <!-- Audit Log Table -->
    <VSkeletonLoader
      v-if="isLoading"
      type="table"
    />
    <VTable v-else-if="logs.length" class="audit-table">
      <thead>
        <tr>
          <th style="width: 40px;"></th>
          <th>Action</th>
          <th>Actor</th>
          <th>Target</th>
          <th>Description</th>
          <th>Time</th>
          <th style="width: 100px;">Severity</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td>
            <VIcon
              :icon="getActionIcon(log.action)"
              size="20"
              :color="getSeverityColor(log.severity)"
            />
          </td>
          <td>
            <div class="text-body-2 font-weight-medium">
              {{ log.action_display }}
            </div>
            <div class="text-caption text-disabled">
              {{ log.action }}
            </div>
          </td>
          <td>
            <div v-if="log.actor" class="text-body-2">
              {{ log.actor.email }}
            </div>
            <div v-else class="text-disabled">System</div>
          </td>
          <td>
            <div v-if="log.target_name" class="text-body-2">
              {{ log.target_name }}
            </div>
            <div v-else class="text-disabled">—</div>
          </td>
          <td>
            <div class="text-body-2" style="max-width: 400px;">
              {{ log.description || '—' }}
            </div>
            <div v-if="log.ip_address" class="text-caption text-disabled">
              IP: {{ log.ip_address }}
            </div>
          </td>
          <td>
            <div class="text-body-2">
              {{ formatDate(log.created_at) }}
            </div>
          </td>
          <td>
            <VChip
              :color="getSeverityColor(log.severity)"
              size="small"
              variant="tonal"
            >
              {{ log.severity }}
            </VChip>
          </td>
        </tr>
      </tbody>
    </VTable>
    <div v-else class="text-center pa-8">
      <VIcon
        icon="ri-file-list-line"
        size="48"
        color="grey"
      />
      <p class="text-body-1 mt-4 text-disabled">
        No audit logs found
      </p>
    </div>

    <!-- Pagination -->
    <VDivider v-if="logs.length" />
    <VCardText v-if="logs.length" class="d-flex align-center justify-space-between">
      <div class="text-body-2 text-disabled">
        Showing {{ (currentPage - 1) * pageSize + 1 }} to {{ Math.min(currentPage * pageSize, totalCount) }} of {{ totalCount }} logs
      </div>
      <VPagination
        v-model="currentPage"
        :length="totalPages"
        :total-visible="5"
        size="small"
        @update:model-value="handlePageChange"
      />
    </VCardText>
  </VCard>
</template>

<style scoped lang="scss">
.audit-table {
  th {
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  tbody tr {
    &:hover {
      background-color: rgba(var(--v-theme-on-surface), 0.04);
    }
  }
}
</style>
