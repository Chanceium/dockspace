<template>
  <v-navigation-drawer
    v-model="drawer"
    :width="280"
    class="mail-sidebar"
  >
    <div class="pa-4">
      <v-btn
        color="primary"
        block
        size="large"
        prepend-icon="ri-edit-line"
        @click="$emit('compose')"
      >
        Compose
      </v-btn>
    </div>

    <v-divider />

    <v-list class="py-0">
      <!-- Folder Navigation -->
      <v-list-item
        v-for="folder in folders"
        :key="folder.value"
        :active="selectedFolder === folder.value"
        :prepend-icon="folder.icon"
        :title="folder.name"
        :value="folder.value"
        @click="$emit('select-folder', folder.value)"
      >
        <template #append>
          <v-chip
            v-if="folder.count > 0"
            size="small"
            :color="folder.value === 'inbox' && folder.count > 0 ? 'primary' : 'default'"
          >
            {{ folder.count }}
          </v-chip>
        </template>
      </v-list-item>
    </v-list>

    <v-divider class="my-2" />

    <!-- Mailboxes Section -->
    <div class="px-4 py-2 d-flex align-center justify-space-between">
      <span class="text-caption text-medium-emphasis">MAILBOXES</span>
      <v-btn
        icon="ri-add-line"
        size="x-small"
        variant="text"
        @click="$emit('add-mailbox')"
      />
    </div>

    <v-list class="py-0">
      <v-list-group
        v-for="mailbox in mailboxes"
        :key="mailbox.id"
        :value="mailbox.id"
      >
        <template #activator="{ props }">
          <v-list-item
            v-bind="props"
            :prepend-icon="`ri-mail-line`"
            :title="mailbox.name"
          >
            <template #prepend>
              <v-badge
                :color="mailbox.color"
                dot
                inline
              />
            </template>
            <template #append>
              <v-btn
                icon="ri-settings-3-line"
                size="x-small"
                variant="text"
                @click.stop="$emit('edit-mailbox', mailbox)"
              />
            </template>
          </v-list-item>
        </template>

        <v-list-item
          :subtitle="mailbox.email"
          density="compact"
        >
          <template #prepend>
            <v-icon
              :color="mailbox.hasError ? 'error' : 'success'"
              size="small"
            >
              {{ mailbox.hasError ? 'ri-error-warning-line' : 'ri-checkbox-circle-line' }}
            </v-icon>
          </template>
        </v-list-item>

        <v-list-item
          v-if="mailbox.hasError"
          density="compact"
        >
          <v-alert
            density="compact"
            type="error"
            variant="tonal"
          >
            {{ mailbox.errorMessage }}
          </v-alert>
        </v-list-item>
      </v-list-group>
    </v-list>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Mailbox, Folder } from '@/services/mailClient'

interface Props {
  folders: Folder[]
  mailboxes: Mailbox[]
  selectedFolder: string
}

defineProps<Props>()

defineEmits<{
  compose: []
  'select-folder': [folder: string]
  'add-mailbox': []
  'edit-mailbox': [mailbox: Mailbox]
}>()

const drawer = ref(true)
</script>

<style scoped>
.mail-sidebar {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
