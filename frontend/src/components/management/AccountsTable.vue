<script setup lang="ts">
import type { MailAccount } from '@/services/mail'

interface Props {
  accounts: MailAccount[]
  loading?: boolean
  currentUserEmail?: string
}

interface Emits {
  (e: 'view', account: MailAccount): void
  (e: 'edit', account: MailAccount): void
  (e: 'delete', account: MailAccount): void
  (e: 'toggle-status', account: MailAccount): void
  (e: 'reset-password', account: MailAccount): void
}

const props = withDefaults(defineProps<Props>(), {
  currentUserEmail: '',
})
const emit = defineEmits<Emits>()

const resolveRoleVariant = (isAdmin: boolean) => {
  return isAdmin ? 'primary' : 'default'
}

const resolveStatusVariant = (status: string) => {
  const statusLower = status.toLowerCase()
  if (statusLower === 'active') return 'success'
  if (statusLower === 'suspended') return 'warning'
  if (statusLower === 'deactivated') return 'error'
  return 'default'
}

const formatStatusLabel = (status: string) => {
  if (!status) return ''
  return status.charAt(0).toUpperCase() + status.slice(1)
}

const isSuspended = (status: string) => status.toLowerCase() === 'suspended'
const isDeactivated = (status: string) => status.toLowerCase() === 'deactivated'

const formatDate = (dateString: string | null) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>

<template>
  <VCard>
    <VCardTitle class="d-flex align-center justify-space-between pa-4">
      <span>Mail Accounts</span>
      <div class="d-flex align-center justify-end w-100">
        <slot name="actions" />
      </div>
    </VCardTitle>

    <VDivider />

    <VCardText class="pa-0">
      <VSkeletonLoader
        v-if="loading"
        type="table-row@5"
      />
      <VTable v-else-if="accounts.length > 0">
        <thead>
          <tr>
            <th>Email</th>
            <th>Name</th>
            <th>Username</th>
            <th>Role</th>
            <th>Status</th>
            <th>Quota</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="account in accounts"
            :key="account.id"
            class="cursor-pointer"
            @click="emit('view', account)"
          >
            <td>{{ account.email }}</td>
            <td>{{ account.first_name }} {{ account.last_name }}</td>
            <td>{{ account.username }}</td>
            <td>
              <VChip
                :color="resolveRoleVariant(account.is_admin)"
                size="small"
                variant="tonal"
              >
                {{ account.is_admin ? 'Admin' : 'User' }}
              </VChip>
            </td>
            <td>
              <VChip
                :color="resolveStatusVariant(account.status)"
                size="small"
                variant="tonal"
              >
                {{ formatStatusLabel(account.status) }}
              </VChip>
            </td>
            <td>{{ account.quota || 'No quota' }}</td>
            <td>{{ formatDate(account.created_at) }}</td>
            <td>
              <VBtn
                icon="ri-pencil-line"
                variant="text"
                size="small"
                @click.stop="emit('edit', account)"
              />
              <VBtn
                icon="ri-key-2-line"
                variant="text"
                size="small"
                color="primary"
                :disabled="account.is_admin || account.email.toLowerCase() === props.currentUserEmail.toLowerCase()"
                :title="account.is_admin ? 'Cannot reset admin password' : 'Reset password'"
                @click.stop="emit('reset-password', account)"
              />
              <VBtn
                icon="ri-forbid-2-line"
                variant="text"
                size="small"
                color="warning"
                :title="isSuspended(account.status) ? 'Reactivate' : 'Suspend'"
                :disabled="account.email.toLowerCase() === props.currentUserEmail.toLowerCase() || isDeactivated(account.status)"
                @click.stop="emit('toggle-status', account)"
              />
              <VBtn
                icon="ri-delete-bin-line"
                variant="text"
                size="small"
                color="error"
                :disabled="account.is_admin || account.email.toLowerCase() === props.currentUserEmail.toLowerCase()"
                @click.stop="emit('delete', account)"
              />
            </td>
          </tr>
        </tbody>
      </VTable>
      <div
        v-else
        class="text-center pa-8"
      >
        <VIcon
          icon="ri-user-line"
          size="48"
          color="grey"
        />
        <p class="text-body-1 mt-4 text-disabled">
          No accounts found
        </p>
      </div>
    </VCardText>
  </VCard>
</template>
