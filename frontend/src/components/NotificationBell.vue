<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { notificationService, type Notification } from '@/services/notifications'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)

const notifications = ref<Notification[]>([])
const unreadCount = ref(0)
const isLoading = ref(false)
const isOpen = ref(false)

// Poll interval (refresh every 30 seconds)
let pollInterval: ReturnType<typeof setInterval> | null = null

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1)
    return 'Just now'
  if (diffMins < 60)
    return `${diffMins}m ago`
  if (diffHours < 24)
    return `${diffHours}h ago`
  if (diffDays < 7)
    return `${diffDays}d ago`

  return date.toLocaleDateString()
}

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

const getIcon = (notification: Notification) => {
  if (notification.action.startsWith('auth.'))
    return 'ri-lock-line'
  if (notification.action.startsWith('account.'))
    return 'ri-user-line'
  if (notification.action.startsWith('group.'))
    return 'ri-group-line'
  if (notification.action.startsWith('oidc.'))
    return 'ri-shield-keyhole-line'
  if (notification.action.startsWith('settings.'))
    return 'ri-settings-line'

  return 'ri-information-line'
}

const loadNotifications = async () => {
  isLoading.value = true
  const response = await notificationService.getNotifications()

  if (response.success && response.notifications) {
    notifications.value = response.notifications
    unreadCount.value = response.unread_count || 0
  }
  isLoading.value = false
}

const loadUnreadCount = async () => {
  const response = await notificationService.getUnreadCount()

  if (response.success && response.count !== undefined)
    unreadCount.value = response.count
}

const onMenuOpen = () => {
  isOpen.value = true
  loadNotifications()
}

const onMenuClose = () => {
  isOpen.value = false
}

const removeNotification = async (id: number) => {
  // Optimistically remove from UI
  notifications.value = notifications.value.filter(n => n.id !== id)
  unreadCount.value = Math.max(0, unreadCount.value - 1)

  // Close dropdown if we just removed the final item
  if (notifications.value.length === 0)
    onMenuClose()

  // Persist dismissal to backend
  const response = await notificationService.dismissNotification(id)

  if (!response.success) {
    // If backend fails, reload notifications to restore state
    console.error('Failed to dismiss notification:', response.error)
    loadNotifications()
  }
}

// Start polling when component mounts
onMounted(() => {
  loadUnreadCount()

  // Poll every 30 seconds
  pollInterval = setInterval(() => {
    loadUnreadCount()
  }, 30000)
})

// Clean up interval when component unmounts
onUnmounted(() => {
  if (pollInterval)
    clearInterval(pollInterval)
})
</script>

<template>
  <VMenu
    v-model="isOpen"
    location="bottom end"
    offset="14px"
    width="420"
    :close-on-content-click="false"
    @update:model-value="(val) => val ? onMenuOpen() : onMenuClose()"
  >
    <template #activator="{ props }">
      <VBadge
        :content="unreadCount"
        :model-value="unreadCount > 0"
        color="primary"
        overlap
        bordered
        v-bind="props"
      >
        <IconBtn>
          <VIcon icon="ri-notification-line" />
        </IconBtn>
      </VBadge>
    </template>

    <VCard class="notifications-card">
      <VCardTitle class="d-flex align-center justify-space-between pa-4">
        <span>Notifications</span>
        <VChip
          v-if="unreadCount > 0"
          size="small"
          color="primary"
          variant="tonal"
        >
          {{ unreadCount }}
        </VChip>
      </VCardTitle>

      <VDivider />

      <div v-if="isLoading" class="pa-6 text-center">
        <VProgressCircular indeterminate color="primary" />
      </div>

      <div v-else-if="notifications.length === 0" class="pa-6 text-center">
        <VIcon
          icon="ri-notification-off-line"
          size="48"
          color="grey"
        />
        <p class="text-body-1 mt-4 text-disabled">
          No notifications
        </p>
      </div>

      <div v-else class="notifications-list">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-item"
        >
          <div class="notification-icon">
            <VIcon
              :icon="getIcon(notification)"
              size="20"
              :color="getSeverityColor(notification.severity)"
            />
          </div>
          <div class="notification-content flex-grow-1">
            <div class="d-flex align-center justify-space-between mb-1">
              <div class="d-flex align-center gap-2">
                <span class="font-weight-medium text-body-2">
                  {{ notification.action_display }}
                </span>
                <VChip
                  v-if="notification.is_admin_only && isAdmin"
                  size="x-small"
                  color="warning"
                  variant="tonal"
                >
                  Admin
                </VChip>
                <VChip
                  v-if="notification.is_personal"
                  size="x-small"
                  color="success"
                  variant="tonal"
                >
                  You
                </VChip>
              </div>
              <IconBtn
                size="small"
                @click="removeNotification(notification.id)"
              >
                <VIcon icon="ri-close-line" size="18" />
              </IconBtn>
            </div>
            <div class="text-body-2 text-medium-emphasis mb-1">
              {{ notification.description }}
            </div>
            <div class="d-flex align-center justify-space-between">
              <span class="text-caption text-disabled">
                {{ formatTime(notification.created_at) }}
              </span>
              <VChip
                v-if="notification.actor"
                size="x-small"
                variant="text"
                class="text-caption"
              >
                <VIcon icon="ri-user-line" size="14" class="me-1" />
                {{ notification.actor.name }}
              </VChip>
            </div>
          </div>
        </div>
      </div>

      <template v-if="notifications.length > 0">
        <VDivider />

        <VCardActions class="justify-center pa-3">
          <VBtn
            variant="text"
            size="small"
            to="/management?tab=application-settings"
          >
            View all in Audit History
          </VBtn>
        </VCardActions>
      </template>
    </VCard>
  </VMenu>
</template>

<style scoped lang="scss">
.notifications-card {
  max-block-size: 520px;
}

.notifications-list {
  max-block-size: 400px;
  overflow-y: auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  border-radius: 8px;
  transition: background-color 0.2s;

  &:hover {
    background-color: rgba(var(--v-theme-on-surface), 0.04);
  }
}

.notification-icon {
  padding-block-start: 2px;
}

.notification-content {
  min-width: 0;
}
</style>
