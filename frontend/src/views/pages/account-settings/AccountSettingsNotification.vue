<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { notificationService, type NotificationPreferences } from '@/services/notifications'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)

const notificationPreferences = ref<NotificationPreferences>({
  // System notifications
  systemChanges: { email: true, browser: true },
  accountActivity: { email: true, browser: true },

  // Management notifications (for admins)
  accountCreated: { email: true, browser: false },
  accountDeleted: { email: true, browser: false },
  groupChanges: { email: false, browser: false },
  settingsChanged: { email: true, browser: false },
  oidcClientChanges: { email: true, browser: false },

  // Security notifications
  newDeviceLogin: { email: true, browser: true },
  passwordChanged: { email: true, browser: true },
  twoFactorChanged: { email: true, browser: true },
  suspiciousActivity: { email: true, browser: true },
})

const selectedNotification = ref('Only when I\'m online')
const isSaving = ref(false)
const smtpConfigured = ref(false)

const savePreferences = async () => {
  isSaving.value = true
  const response = await notificationService.updatePreferences(notificationPreferences.value)

  if (response.success) {
    // Show success message (could use a toast notification)
    console.log('Notification preferences saved successfully')
  }
  else {
    console.error('Failed to save notification preferences:', response.error)
  }
  isSaving.value = false
}

const resetPreferences = () => {
  // Reset to defaults
  notificationPreferences.value = {
    systemChanges: { email: true, browser: true },
    accountActivity: { email: true, browser: true },
    accountCreated: { email: true, browser: false },
    accountDeleted: { email: true, browser: false },
    groupChanges: { email: false, browser: false },
    settingsChanged: { email: true, browser: false },
    oidcClientChanges: { email: true, browser: false },
    newDeviceLogin: { email: true, browser: true },
    passwordChanged: { email: true, browser: true },
    twoFactorChanged: { email: true, browser: true },
    suspiciousActivity: { email: true, browser: true },
  }
}

const loadPreferences = async () => {
  const response = await notificationService.getPreferences()

  if (response.success && response.preferences)
    notificationPreferences.value = response.preferences
}

const checkSmtpStatus = async () => {
  const response = await notificationService.checkSmtpStatus()

  if (response.success && response.smtp_configured !== undefined)
    smtpConfigured.value = response.smtp_configured
}

onMounted(() => {
  loadPreferences()
  checkSmtpStatus()
})
</script>

<template>
  <VCard title="Notification Preferences">
    <!-- System Notifications -->
    <VCardText>
      <div class="text-h6 mb-4">System Notifications</div>
      <VTable class="text-no-wrap notification-table">
        <thead>
          <tr>
            <th scope="col">Type</th>
            <th scope="col" class="text-center" style="width: 100px;">EMAIL</th>
            <th scope="col" class="text-center" style="width: 100px;">BROWSER</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-information-line" size="20" />
                <div>
                  <div class="font-weight-medium">System Changes</div>
                  <div class="text-caption text-disabled">Application updates and maintenance</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.systemChanges.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.systemChanges.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-user-line" size="20" />
                <div>
                  <div class="font-weight-medium">Account Activity</div>
                  <div class="text-caption text-disabled">Changes to your account</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.accountActivity.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.accountActivity.browser" hide-details />
            </td>
          </tr>
        </tbody>
      </VTable>
    </VCardText>

    <VDivider />

    <!-- Management Notifications -->
    <VCardText>
      <div class="text-h6 mb-4">Management Events (Admin Only)</div>
      <VTable class="text-no-wrap notification-table">
        <thead>
          <tr>
            <th scope="col">Type</th>
            <th scope="col" class="text-center" style="width: 100px;">EMAIL</th>
            <th scope="col" class="text-center" style="width: 100px;">BROWSER</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-user-add-line" size="20" />
                <div>
                  <div class="font-weight-medium">Account Created</div>
                  <div class="text-caption text-disabled">New mail accounts created</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.accountCreated.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.accountCreated.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-user-unfollow-line" size="20" />
                <div>
                  <div class="font-weight-medium">Account Deleted</div>
                  <div class="text-caption text-disabled">Mail accounts deleted</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.accountDeleted.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.accountDeleted.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-group-line" size="20" />
                <div>
                  <div class="font-weight-medium">Group Changes</div>
                  <div class="text-caption text-disabled">Group creation, updates, deletions</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.groupChanges.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.groupChanges.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-settings-line" size="20" />
                <div>
                  <div class="font-weight-medium">Settings Changed</div>
                  <div class="text-caption text-disabled">Application or SMTP settings modified</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.settingsChanged.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.settingsChanged.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-shield-keyhole-line" size="20" />
                <div>
                  <div class="font-weight-medium">OIDC Client Changes</div>
                  <div class="text-caption text-disabled">OIDC client modifications</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.oidcClientChanges.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.oidcClientChanges.browser" hide-details />
            </td>
          </tr>
        </tbody>
      </VTable>
    </VCardText>

    <VDivider />

    <!-- Security Notifications -->
    <VCardText>
      <div class="text-h6 mb-4">Security Alerts</div>
      <VTable class="text-no-wrap notification-table">
        <thead>
          <tr>
            <th scope="col">Type</th>
            <th scope="col" class="text-center" style="width: 100px;">EMAIL</th>
            <th scope="col" class="text-center" style="width: 100px;">BROWSER</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-device-line" size="20" color="warning" />
                <div>
                  <div class="font-weight-medium">New Device Login</div>
                  <div class="text-caption text-disabled">Login from unrecognized device</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.newDeviceLogin.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.newDeviceLogin.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-lock-password-line" size="20" color="warning" />
                <div>
                  <div class="font-weight-medium">Password Changed</div>
                  <div class="text-caption text-disabled">Account password modified</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.passwordChanged.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.passwordChanged.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-shield-check-line" size="20" color="warning" />
                <div>
                  <div class="font-weight-medium">Two-Factor Authentication</div>
                  <div class="text-caption text-disabled">2FA enabled or disabled</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.twoFactorChanged.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.twoFactorChanged.browser" hide-details />
            </td>
          </tr>
          <tr>
            <td>
              <div class="d-flex align-center gap-2">
                <VIcon icon="ri-alert-line" size="20" color="error" />
                <div>
                  <div class="font-weight-medium">Suspicious Activity</div>
                  <div class="text-caption text-disabled">Potential security threats detected</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.suspiciousActivity.email" hide-details :disabled="!smtpConfigured" />
            </td>
            <td class="text-center">
              <VCheckbox v-model="notificationPreferences.suspiciousActivity.browser" hide-details />
            </td>
          </tr>
        </tbody>
      </VTable>
    </VCardText>

    <VDivider />

    <VCardText>
      <VForm @submit.prevent="savePreferences">
        <div class="d-flex flex-wrap gap-4 mt-4">
          <VBtn type="submit" :loading="isSaving">
            Save Changes
          </VBtn>
          <VBtn
            color="secondary"
            variant="outlined"
            type="reset"
            @click="resetPreferences"
          >
            Reset
          </VBtn>
        </div>
      </VForm>
    </VCardText>
  </VCard>
</template>

<style scoped lang="scss">
.notification-table {
  tbody tr:hover {
    background-color: rgba(var(--v-theme-on-surface), 0.04);
  }

  th {
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
  }
}
</style>
