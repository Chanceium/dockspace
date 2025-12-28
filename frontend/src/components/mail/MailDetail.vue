<template>
  <div
    v-if="email"
    class="mail-detail"
  >
    <!-- Toolbar -->
    <v-toolbar
      density="compact"
      flat
      class="border-b"
    >
      <v-btn
        icon="ri-arrow-left-line"
        @click="$emit('close')"
      />

      <v-spacer />

      <v-btn
        icon="ri-reply-line"
        @click="$emit('reply')"
      />

      <v-btn
        icon="ri-share-forward-line"
        @click="$emit('forward')"
      />

      <v-btn
        icon="ri-delete-bin-line"
        @click="$emit('delete')"
      />

      <v-menu>
        <template #activator="{ props }">
          <v-btn
            icon="ri-more-2-line"
            v-bind="props"
          />
        </template>

        <v-list>
          <v-list-item @click="$emit('mark-unread')">
            <template #prepend>
              <v-icon>ri-mail-line</v-icon>
            </template>
            <v-list-item-title>Mark as unread</v-list-item-title>
          </v-list-item>

          <v-list-item @click="$emit('toggle-star')">
            <template #prepend>
              <v-icon>ri-star-line</v-icon>
            </template>
            <v-list-item-title>{{ email.starred ? 'Unstar' : 'Star' }}</v-list-item-title>
          </v-list-item>

          <v-list-item @click="$emit('archive')">
            <template #prepend>
              <v-icon>ri-archive-line</v-icon>
            </template>
            <v-list-item-title>Archive</v-list-item-title>
          </v-list-item>

          <v-list-item @click="$emit('move-to-spam')">
            <template #prepend>
              <v-icon>ri-spam-line</v-icon>
            </template>
            <v-list-item-title>Move to spam</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-toolbar>

    <!-- Email Header -->
    <div class="pa-6">
      <div class="d-flex align-center mb-4">
        <v-avatar
          color="primary"
          size="48"
        >
          <span class="text-h6">
            {{ email.from.charAt(0).toUpperCase() }}
          </span>
        </v-avatar>

        <div class="ml-4 flex-grow-1">
          <div class="d-flex align-center">
            <h2 class="text-h6">
              {{ email.subject }}
            </h2>
            <v-spacer />
            <v-btn
              :icon="email.starred ? 'ri-star-fill' : 'ri-star-line'"
              :color="email.starred ? 'warning' : 'default'"
              size="small"
              variant="text"
              @click="$emit('toggle-star')"
            />
          </div>

          <div class="d-flex align-center mt-1 text-body-2 text-medium-emphasis">
            <span class="font-weight-medium text-body-1">{{ email.from }}</span>
            <span class="mx-2">&lt;{{ email.fromEmail }}&gt;</span>
          </div>

          <div class="d-flex align-center mt-1 text-caption text-medium-emphasis">
            <span>to {{ email.to }}</span>
            <span
              v-if="email.cc"
              class="ml-2"
            >
              cc {{ email.cc }}
            </span>
            <v-spacer />
            <span>{{ email.date }} {{ email.time }}</span>
          </div>
        </div>
      </div>

      <!-- Email Body -->
      <v-divider class="my-4" />

      <div
        v-if="email.bodyHtml"
        class="email-body"
        v-html="email.bodyHtml"
      />
      <div
        v-else
        class="email-body"
        style="white-space: pre-wrap;"
      >
        {{ email.body }}
      </div>

      <!-- Attachments -->
      <div
        v-if="email.attachments && email.attachments.length > 0"
        class="mt-6"
      >
        <v-divider class="mb-4" />
        <h3 class="text-subtitle-2 mb-2">
          Attachments ({{ email.attachments.length }})
        </h3>
        <v-list class="pa-0">
          <v-list-item
            v-for="(attachment, index) in email.attachments"
            :key="index"
            class="border rounded mb-2"
          >
            <template #prepend>
              <v-icon>ri-file-line</v-icon>
            </template>

            <v-list-item-title>{{ attachment.name }}</v-list-item-title>
            <v-list-item-subtitle>{{ formatSize(attachment.size) }}</v-list-item-subtitle>

            <template #append>
              <v-btn
                icon="ri-download-line"
                size="small"
                variant="text"
              />
            </template>
          </v-list-item>
        </v-list>
      </div>
    </div>
  </div>

  <!-- Empty State -->
  <div
    v-else
    class="d-flex flex-column align-center justify-center pa-8"
    style="height: 100%;"
  >
    <v-icon
      size="96"
      color="grey-lighten-1"
    >
      ri-mail-open-line
    </v-icon>
    <p class="text-h6 mt-4 text-medium-emphasis">
      Select an email to read
    </p>
    <p class="text-caption text-medium-emphasis">
      Choose an email from the list to view its contents
    </p>
  </div>
</template>

<script setup lang="ts">
import type { EmailDetail } from '@/services/mailClient'

interface Props {
  email: EmailDetail | null
}

defineProps<Props>()

defineEmits<{
  close: []
  reply: []
  forward: []
  delete: []
  'mark-unread': []
  'toggle-star': []
  archive: []
  'move-to-spam': []
}>()

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${Math.round(bytes / Math.pow(k, i) * 100) / 100} ${sizes[i]}`
}
</script>

<style scoped>
.mail-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.email-body {
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface));
}

.email-body :deep(a) {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}

.email-body :deep(a):hover {
  text-decoration: underline;
}
</style>
