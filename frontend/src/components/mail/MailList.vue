<template>
  <div class="mail-list">
    <!-- Toolbar -->
    <v-toolbar
      density="compact"
      flat
      class="border-b"
    >
      <v-btn
        icon="ri-menu-line"
        @click="$emit('toggle-drawer')"
      />

      <v-text-field
        v-model="searchQuery"
        density="compact"
        placeholder="Search emails..."
        prepend-inner-icon="ri-search-line"
        hide-details
        single-line
        class="mx-4"
        @update:model-value="$emit('search', searchQuery)"
      />

      <v-btn
        icon="ri-refresh-line"
        @click="$emit('refresh')"
      />

      <v-btn
        icon="ri-filter-line"
        @click="showFilters = !showFilters"
      />
    </v-toolbar>

    <!-- Filters -->
    <v-expand-transition>
      <div
        v-if="showFilters"
        class="px-4 py-2 border-b"
      >
        <v-chip-group>
          <v-chip
            :color="filterUnreadOnly ? 'primary' : 'default'"
            @click="$emit('toggle-filter', 'unread')"
          >
            <v-icon start>
              ri-mail-line
            </v-icon>
            Unread only
          </v-chip>

          <v-chip
            :color="filterStarredOnly ? 'primary' : 'default'"
            @click="$emit('toggle-filter', 'starred')"
          >
            <v-icon start>
              ri-star-line
            </v-icon>
            Starred only
          </v-chip>

          <v-chip
            :color="filterHasAttachments ? 'primary' : 'default'"
            @click="$emit('toggle-filter', 'attachments')"
          >
            <v-icon start>
              ri-attachment-line
            </v-icon>
            Has attachments
          </v-chip>
        </v-chip-group>
      </div>
    </v-expand-transition>

    <!-- Email List -->
    <v-list
      v-if="!loading && emails.length > 0"
      class="email-list pa-0"
    >
      <v-list-item
        v-for="email in emails"
        :key="email.id"
        :active="selectedEmail?.id === email.id"
        class="email-list-item"
        @click="$emit('select-email', email)"
      >
        <template #prepend>
          <v-checkbox
            hide-details
            density="compact"
            @click.stop
          />
        </template>

        <v-list-item-title class="d-flex align-center mb-1">
          <span :class="{ 'font-weight-bold': !email.read }">
            {{ email.from }}
          </span>
          <v-spacer />
          <span class="text-caption text-medium-emphasis">
            {{ email.time || email.date }}
          </span>
        </v-list-item-title>

        <v-list-item-subtitle class="mb-1">
          <span :class="{ 'font-weight-medium': !email.read }">
            {{ email.subject }}
          </span>
        </v-list-item-subtitle>

        <v-list-item-subtitle class="text-caption">
          {{ email.preview }}
        </v-list-item-subtitle>

        <template #append>
          <div class="d-flex flex-column align-center gap-2">
            <v-btn
              :icon="email.starred ? 'ri-star-fill' : 'ri-star-line'"
              :color="email.starred ? 'warning' : 'default'"
              size="x-small"
              variant="text"
              @click.stop="$emit('toggle-star', email)"
            />
            <v-icon
              v-if="email.hasAttachments"
              size="small"
            >
              ri-attachment-line
            </v-icon>
          </div>
        </template>
      </v-list-item>
    </v-list>

    <!-- Loading State -->
    <div
      v-else-if="loading"
      class="d-flex align-center justify-center pa-8"
    >
      <v-progress-circular
        indeterminate
        color="primary"
      />
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="d-flex flex-column align-center justify-center pa-8"
    >
      <v-icon
        size="64"
        color="grey-lighten-1"
      >
        ri-mail-line
      </v-icon>
      <p class="text-h6 mt-4 text-medium-emphasis">
        No emails found
      </p>
      <p class="text-caption text-medium-emphasis">
        This folder is empty
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Email } from '@/services/mailClient'

interface Props {
  emails: Email[]
  selectedEmail: Email | null
  loading: boolean
  filterUnreadOnly?: boolean
  filterStarredOnly?: boolean
  filterHasAttachments?: boolean
}

defineProps<Props>()

defineEmits<{
  'toggle-drawer': []
  search: [query: string]
  refresh: []
  'toggle-filter': [filter: 'unread' | 'starred' | 'attachments']
  'select-email': [email: Email]
  'toggle-star': [email: Email]
}>()

const searchQuery = ref('')
const showFilters = ref(false)
</script>

<style scoped>
.mail-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.email-list {
  overflow-y: auto;
  flex: 1;
}

.email-list-item {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  cursor: pointer;
  transition: background-color 0.2s;
}

.email-list-item:hover {
  background-color: rgba(var(--v-theme-surface-variant), 0.12);
}
</style>
