<script setup lang="ts">
import type { MailAccount, MailGroup } from '@/services/mail'

interface Props {
  isOpen: boolean
  group: MailGroup | null
  members: MailAccount[]
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'removeMember', member: MailAccount): void
}>()
</script>

<template>
  <VDialog
    :model-value="isOpen"
    max-width="700"
    @update:model-value="emit('update:isOpen', $event)"
  >
    <VCard>
      <VCardTitle class="d-flex align-center justify-space-between pa-4">
        <div class="d-flex align-center gap-2">
          <VAvatar color="info" variant="tonal">
            <VIcon icon="ri-group-line" />
          </VAvatar>
          <div class="d-flex flex-column">
            <span class="text-subtitle-1">{{ group?.name || 'Group' }}</span>
            <span class="text-caption text-disabled">{{ group?.description }}</span>
          </div>
        </div>
        <VBtn
          icon="ri-close-line"
          variant="text"
          size="small"
          @click="emit('update:isOpen', false)"
        />
      </VCardTitle>
      <VDivider />
      <VCardText class="pa-6">
        <div class="text-body-2 text-disabled mb-2 d-flex align-center gap-2">
          <VIcon icon="ri-user-3-line" size="18" />
          Members
        </div>
        <VList
          v-if="members.length"
          density="compact"
          class="border rounded"
        >
          <VListItem
            v-for="member in members"
            :key="member.id"
            :title="member.email"
            :subtitle="member.username"
          >
            <template #append>
              <VBtn
                icon="ri-delete-bin-line"
                variant="text"
                size="small"
                color="error"
                @click.stop="emit('removeMember', member)"
              />
            </template>
          </VListItem>
        </VList>
        <div v-else class="text-disabled">No members</div>
      </VCardText>
    </VCard>
  </VDialog>
</template>
