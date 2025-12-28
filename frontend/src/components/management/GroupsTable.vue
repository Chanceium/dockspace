<script setup lang="ts">
import type { MailGroup } from '@/services/mail'

interface Props {
  groups: MailGroup[]
  loading?: boolean
}

interface Emits {
  (e: 'edit', group: MailGroup): void
  (e: 'delete', group: MailGroup): void
  (e: 'view', group: MailGroup): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formatDate = (dateString?: string | null) => {
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
      <span>Mail Groups</span>
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
      <VTable v-else-if="groups.length > 0">
        <thead>
          <tr>
            <th>Name</th>
            <th>Description</th>
            <th>Members</th>
            <th>Created</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="group in groups"
            :key="group.id"
            class="cursor-pointer"
            @click="emit('view', group)"
          >
            <td class="font-weight-medium">
              {{ group.name }}
            </td>
            <td>{{ group.description || 'No description' }}</td>
            <td>
              <VChip
                size="small"
                variant="tonal"
              >
                {{ group.member_count }} members
              </VChip>
            </td>
            <td>{{ formatDate(group.created_at) }}</td>
            <td>{{ formatDate(group.updated_at) }}</td>
            <td>
              <VBtn
                icon="ri-pencil-line"
                variant="text"
                size="small"
                @click.stop="emit('edit', group)"
              />
              <VBtn
                icon="ri-delete-bin-line"
                variant="text"
                size="small"
                color="error"
                @click.stop="emit('delete', group)"
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
          icon="ri-group-line"
          size="48"
          color="grey"
        />
        <p class="text-body-1 mt-4 text-disabled">
          No groups found
        </p>
      </div>
    </VCardText>
  </VCard>
</template>
