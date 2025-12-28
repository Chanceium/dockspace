<script setup lang="ts">
import type { MailAccount, MailAlias, MailGroup } from '@/services/mail'

interface Props {
  isOpen: boolean
  account: MailAccount | null
  aliases: MailAlias[]
  groups: MailGroup[]
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'removeAlias', alias: MailAlias): void
  (e: 'removeGroup', groupId: number): void
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
          <VAvatar color="primary" variant="tonal">
            <VIcon icon="ri-user-line" />
          </VAvatar>
          <div class="d-flex flex-column">
            <span class="text-subtitle-1">{{ account?.email || 'Account' }}</span>
            <span class="text-caption text-disabled">{{ account?.username }}</span>
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
        <VRow dense>
          <VCol cols="12" md="6">
            <div class="text-body-2 text-disabled mb-2 d-flex align-center gap-2">
              <VIcon icon="ri-group-line" size="18" />
              Groups
            </div>
            <div v-if="groups.length" class="d-flex flex-column gap-2">
              <VChip
                v-for="group in groups"
                :key="group.id"
                class="justify-space-between"
                closable
                color="primary"
                variant="tonal"
                @click:close="emit('removeGroup', group.id)"
              >
                {{ group.name }}
              </VChip>
            </div>
            <div v-else class="text-disabled">No groups</div>
          </VCol>
          <VCol cols="12" md="6">
            <div class="text-body-2 text-disabled mb-2 d-flex align-center gap-2">
              <VIcon icon="ri-mail-send-line" size="18" />
              Aliases
            </div>
            <VList
              v-if="aliases.length"
              density="compact"
              class="border rounded"
            >
              <VListItem
                v-for="alias in aliases"
                :key="alias.id"
                :title="alias.alias_email"
                :subtitle="`→ ${alias.destination_email}`"
              >
                <template #append>
                  <VBtn
                    icon="ri-delete-bin-line"
                    variant="text"
                    size="small"
                    color="error"
                    @click.stop="emit('removeAlias', alias)"
                  />
                </template>
              </VListItem>
            </VList>
            <div v-else class="text-disabled">No aliases</div>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>
  </VDialog>
</template>
