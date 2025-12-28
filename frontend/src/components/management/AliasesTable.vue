<script setup lang="ts">
import type { MailAlias } from '@/services/mail'

interface Props {
  aliases: MailAlias[]
  loading?: boolean
}

interface Emits {
  (e: 'delete', alias: MailAlias): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formatDate = (dateString?: string) => {
  if (!dateString) return '—'
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return '—'
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
      <span>Mail Aliases</span>
      <div class="d-flex align-center justify-end w-100">
        <slot name="actions" />
      </div>
    </VCardTitle>

    <VDivider />

    <VCardText class="pa-0">
      <VSkeletonLoader
        v-if="loading"
        type="table-row@3"
      />
      <VTable v-else-if="aliases.length > 0">
        <thead>
          <tr>
            <th>Alias Email</th>
            <th>Destination Email</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="alias in aliases"
            :key="alias.id"
          >
            <td>{{ alias.alias_email }}</td>
            <td>{{ alias.destination_email }}</td>
            <td>{{ formatDate(alias.created_at) }}</td>
            <td>
              <VBtn
                icon="ri-delete-bin-line"
                variant="text"
                size="small"
                color="error"
                @click="emit('delete', alias)"
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
          icon="ri-mail-line"
          size="48"
          color="grey"
        />
        <p class="text-body-1 mt-4 text-disabled">
          No aliases found
        </p>
      </div>
    </VCardText>
  </VCard>
</template>
