<script setup lang="ts">
import type { OIDCClient } from '@/services/oidc'

interface Props {
  clients: OIDCClient[]
  loading?: boolean
  errorMessage?: string
  successMessage?: string
}

withDefaults(defineProps<Props>(), {
  loading: false,
  errorMessage: '',
  successMessage: '',
})

const emit = defineEmits<{
  (e: 'add'): void
  (e: 'edit', client: OIDCClient): void
  (e: 'delete', client: OIDCClient): void
}>()
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle>OIDC clients</VCardTitle>
      <template #append>
        <VBtn
          color="primary"
          variant="outlined"
          @click="emit('add')"
        >
          Add client
        </VBtn>
      </template>
    </VCardItem>
    <VCardText>
      <VAlert
        v-if="errorMessage"
        type="error"
        variant="tonal"
        class="mb-4"
      >
        {{ errorMessage }}
      </VAlert>
      <VAlert
        v-else-if="successMessage"
        type="success"
        variant="tonal"
        class="mb-4"
      >
        {{ successMessage }}
      </VAlert>
      <VSkeletonLoader
        v-if="loading"
        type="table"
      />
      <VTable v-else-if="clients.length">
        <thead>
          <tr>
            <th>Name</th>
            <th>Client ID</th>
            <th>Groups</th>
            <th>2FA</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="client in clients"
            :key="client.id"
          >
            <td class="font-weight-medium">{{ client.name }}</td>
            <td><code>{{ client.client_id }}</code></td>
            <td>{{ client.group_count || 0 }}</td>
            <td>
              <VChip
                :color="client.require_2fa ? 'primary' : 'default'"
                size="small"
                variant="tonal"
              >
                {{ client.require_2fa ? 'Required' : 'Optional' }}
              </VChip>
            </td>
            <td>{{ client.created_at ? new Date(client.created_at).toLocaleDateString() : '—' }}</td>
            <td>
              <VBtn
                icon="ri-pencil-line"
                variant="text"
                size="small"
                @click="emit('edit', client)"
              />
              <VBtn
                icon="ri-delete-bin-line"
                variant="text"
                size="small"
                color="error"
                @click="emit('delete', client)"
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
          icon="ri-shield-keyhole-line"
          size="48"
          color="grey"
        />
        <p class="text-body-1 mt-4 text-disabled">
          No OIDC clients yet. Add your first client to get started.
        </p>
      </div>
    </VCardText>
  </VCard>
</template>
