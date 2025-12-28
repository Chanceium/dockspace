<script lang="ts" setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import { profileService } from '@/services/profile'
import ConfirmDialog from '@/@core/components/ConfirmDialog.vue'
import QRCode from 'qrcode'

const isCurrentPasswordVisible = ref(false)
const isNewPasswordVisible = ref(false)
const isConfirmPasswordVisible = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordForm = ref()
const isSubmitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const copyState = ref<'idle' | 'copied' | 'error'>('idle')
let copyTimer: ReturnType<typeof setTimeout> | null = null

const isTwoFactorEnabled = ref(false)

const isCreateDeviceDialogOpen = ref(false)
const newDeviceName = ref('')
const accessCode = ref('')
const isConfirmDeleteOpen = ref(false)
const devicePendingDelete = ref<{ id: number; name: string } | null>(null)
const newDeviceId = ref<number | null>(null)
const newDeviceSecret = ref('')
const newDeviceProvisioningUri = ref('')
const qrCodeDataUrl = ref('')

const passwordRequirements = ref<string[]>([
  'Loading password requirements...',
])

// Fetch password requirements and TOTP status from backend
onMounted(async () => {
  const response = await profileService.getPasswordRequirements()
  if (response.success && response.requirements.length > 0) {
    passwordRequirements.value = response.requirements
  } else {
    // Fallback requirements if API fails
    passwordRequirements.value = [
      'At least 12 characters long',
      'At least one uppercase letter',
      'At least one lowercase letter',
      'At least one digit',
      'At least one special character',
    ]
  }

  // Load TOTP status and devices
  await loadTOTPStatus()

  // Load recent login sessions
  await loadRecentSessions()
})

const generatePassword = () => {
  const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const lower = 'abcdefghijklmnopqrstuvwxyz'
  const numbers = '0123456789'
  const symbols = '!@#$%^&*()-_=+[]{};:,.<>?'
  const all = upper + lower + numbers + symbols

  const pick = (chars: string) => chars[Math.floor(Math.random() * chars.length)]
  const required = [pick(upper), pick(lower), pick(numbers), pick(symbols)]

  const remainingLength = 16 - required.length
  for (let i = 0; i < remainingLength; i++) {
    required.push(pick(all))
  }

  // shuffle for randomness
  for (let i = required.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[required[i], required[j]] = [required[j], required[i]]
  }

  newPassword.value = required.join('')
  confirmPassword.value = newPassword.value
  copyPasswordToClipboard(newPassword.value)
}

const setCopyState = (state: 'idle' | 'copied' | 'error') => {
  copyState.value = state
  if (copyTimer) {
    clearTimeout(copyTimer)
    copyTimer = null
  }
  if (state !== 'idle') {
    copyTimer = setTimeout(() => {
      copyState.value = 'idle'
      copyTimer = null
    }, 1600)
  }
}

const copyPasswordToClipboard = async (password: string) => {
  if (!password) return
  if (!(navigator && navigator.clipboard && navigator.clipboard.writeText)) {
    setCopyState('error')
    return
  }
  try {
    await navigator.clipboard.writeText(password)
    setCopyState('copied')
  } catch (error) {
    console.error('Failed to copy password', error)
    setCopyState('error')
  }
}

onBeforeUnmount(() => {
  if (copyTimer) {
    clearTimeout(copyTimer)
    copyTimer = null
  }
})

// Password validation rules
const currentPasswordRules = [
  (v: string) => !!v || 'Current password is required',
]

const newPasswordRules = [
  (v: string) => !!v || 'New password is required',
  (v: string) => v.length >= 12 || 'Password must be at least 12 characters long',
]

const confirmPasswordRules = [
  (v: string) => !!v || 'Please confirm your new password',
  (v: string) => v === newPassword.value || 'Passwords do not match',
]

// Submit password change
const handlePasswordChange = async () => {
  // Reset messages
  errorMessage.value = ''
  successMessage.value = ''

  // Validate form
  const { valid } = await passwordForm.value.validate()
  if (!valid) {
    return
  }

  isSubmitting.value = true

  try {
    const response = await profileService.changePassword(
      currentPassword.value,
      newPassword.value
    )

    if (response.success) {
      successMessage.value = response.message || 'Password changed successfully'
      // Reset form
      currentPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
      passwordForm.value.reset()
    } else {
      // Handle validation errors from backend
      if (response.errors && response.errors.length > 0) {
        errorMessage.value = response.errors.join('. ')
      } else {
        errorMessage.value = response.error || 'Failed to change password'
      }
    }
  } catch (error) {
    errorMessage.value = 'An unexpected error occurred. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

// Reset password form
const resetPasswordForm = () => {
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  errorMessage.value = ''
  successMessage.value = ''
  passwordForm.value.reset()
}

interface TOTPDevice {
  id: number
  name: string
  verified_at: string | null
  last_used_at: string | null
  created_at: string
}

const totpDevices = ref<TOTPDevice[]>([])

// Load TOTP devices and status
const loadTOTPStatus = async () => {
  const statusResponse = await profileService.getTOTPStatus()
  if (statusResponse.success) {
    isTwoFactorEnabled.value = statusResponse.enabled
  }

  const devicesResponse = await profileService.listTOTPDevices()
  if (devicesResponse.success) {
    totpDevices.value = devicesResponse.devices
  }
}

const requiredDeviceNameRule = (value: string) => {
  return value?.trim().length ? true : 'Device name is required'
}

const requiredAccessCodeRule = (value: string) => {
  return value?.trim().length ? true : 'Access code is required'
}

// Format date for display
const formatDate = (isoString: string | null) => {
  if (!isoString) return 'Never'
  return new Date(isoString).toLocaleString()
}

// Open dialog to create new device - Step 1: Enter device name
const openCreateDeviceDialog = () => {
  newDeviceName.value = ''
  accessCode.value = ''
  newDeviceId.value = null
  newDeviceSecret.value = ''
  newDeviceProvisioningUri.value = ''
  qrCodeDataUrl.value = ''
  isCreateDeviceDialogOpen.value = true
}

// Generate QR code when provisioning URI changes
watch(newDeviceProvisioningUri, async (uri) => {
  if (uri) {
    try {
      qrCodeDataUrl.value = await QRCode.toDataURL(uri, {
        width: 256,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        }
      })
    } catch (error) {
      console.error('Failed to generate QR code:', error)
    }
  }
})

// Create device - Step 2: Generate QR code
const createDevice = async () => {
  if (!newDeviceName.value.trim()) return

  // If we don't have a device ID yet, create the device
  if (!newDeviceId.value) {
    const response = await profileService.createTOTPDevice(newDeviceName.value.trim())
    if (response.success && response.device) {
      newDeviceId.value = response.device.id
      newDeviceSecret.value = response.device.secret
      newDeviceProvisioningUri.value = response.device.provisioning_uri
      // Keep dialog open for QR code scan and verification
      return
    } else {
      alert(response.error || 'Failed to create device')
      return
    }
  }

  // If we have a device ID, verify the token
  if (!accessCode.value.trim()) {
    alert('Please enter the verification code')
    return
  }

  const response = await profileService.verifyTOTPDevice(newDeviceId.value, accessCode.value)
  if (response.success) {
    // Success - reload devices and close dialog
    await loadTOTPStatus()
    closeCreateDeviceDialog()
  } else {
    alert(response.error || 'Invalid verification code')
  }
}

const closeCreateDeviceDialog = () => {
  newDeviceName.value = ''
  accessCode.value = ''
  newDeviceId.value = null
  newDeviceSecret.value = ''
  newDeviceProvisioningUri.value = ''
  qrCodeDataUrl.value = ''
  isCreateDeviceDialogOpen.value = false
}

const requestDeleteDevice = (device: TOTPDevice) => {
  devicePendingDelete.value = device
  isConfirmDeleteOpen.value = true
}

const confirmDeleteDevice = async () => {
  if (!devicePendingDelete.value) return

  const response = await profileService.deleteTOTPDevice(devicePendingDelete.value.id)
  if (response.success) {
    await loadTOTPStatus()
    devicePendingDelete.value = null
    isConfirmDeleteOpen.value = false
  } else {
    alert(response.error || 'Failed to delete device')
  }
}

const recentDevicesHeaders = [
  { title: 'BROWSER', key: 'browser' },
  { title: 'DEVICE', key: 'device' },
  { title: 'LOCATION', key: 'location' },
  { title: 'IP ADDRESS', key: 'ipAddress' },
  { title: 'RECENT ACTIVITY', key: 'recentActivity' },
]

const recentDevices = ref<any[]>([])

// Load recent sessions
const loadRecentSessions = async () => {
  const response = await profileService.listSessions()
  if (response.success) {
    // Map sessions to table format
    recentDevices.value = response.sessions.map(session => ({
      browser: session.browser,
      device: session.device,
      location: session.location,
      ipAddress: session.ip_address,
      recentActivity: formatDate(session.last_activity),
      deviceIcon: getDeviceIcon(session.browser, session.device),
      is_current: session.is_current,
    }))
  }
}

// Get icon based on browser/device
const getDeviceIcon = (browser: string, device: string) => {
  const lowerBrowser = browser.toLowerCase()
  const lowerDevice = device.toLowerCase()

  if (lowerDevice.includes('iphone') || lowerDevice.includes('ipad')) {
    return { icon: 'ri-smartphone-line', color: 'primary' }
  } else if (lowerDevice.includes('android')) {
    return { icon: 'ri-android-line', color: 'success' }
  } else if (lowerDevice.includes('mac')) {
    return { icon: 'ri-mac-line', color: 'secondary' }
  } else if (lowerBrowser.includes('windows')) {
    return { icon: 'ri-macbook-line', color: 'primary' }
  } else {
    return { icon: 'ri-computer-line', color: 'info' }
  }
}
</script>

<template>
  <VRow>
    <!-- SECTION: Change Password -->
    <VCol cols="12">
      <VCard title="Change Password">
        <VForm ref="passwordForm" @submit.prevent="handlePasswordChange">
          <VCardText>
            <!-- Error message -->
            <VAlert
              v-if="errorMessage"
              type="error"
              class="mb-4"
              closable
              @click:close="errorMessage = ''"
            >
              {{ errorMessage }}
            </VAlert>

            <!-- Success message -->
            <VAlert
              v-if="successMessage"
              type="success"
              class="mb-4"
              closable
              @click:close="successMessage = ''"
            >
              {{ successMessage }}
            </VAlert>

            <!-- 👉 Current Password -->
            <VRow class="mb-3">
              <VCol
                cols="12"
                md="6"
              >
                <!-- 👉 current password -->
                <VTextField
                  v-model="currentPassword"
                  :rules="currentPasswordRules"
                  :type="isCurrentPasswordVisible ? 'text' : 'password'"
                  :append-inner-icon="isCurrentPasswordVisible ? 'ri-eye-off-line' : 'ri-eye-line'"
                  autocomplete="current-password"
                  label="Current Password"
                  placeholder="············"
                  @click:append-inner="isCurrentPasswordVisible = !isCurrentPasswordVisible"
                />
              </VCol>
            </VRow>

            <!-- 👉 New Password -->
            <VRow class="mb-3">
              <VCol
                cols="12"
                md="6"
              >
                <!-- 👉 new password -->
                <VTextField
                  v-model="newPassword"
                  :rules="newPasswordRules"
                  :type="isNewPasswordVisible ? 'text' : 'password'"
                  :append-inner-icon="isNewPasswordVisible ? 'ri-eye-off-line' : 'ri-eye-line'"
                  label="New Password"
                  autocomplete="new-password"
                  placeholder="············"
                  @click:append-inner="isNewPasswordVisible = !isNewPasswordVisible"
                />
              </VCol>
            </VRow>

            <!-- 👉 Confirm Password -->
            <VRow class="mb-3">
              <VCol
                cols="12"
                md="6"
              >
                <!-- 👉 confirm password -->
                <VTextField
                  v-model="confirmPassword"
                  :rules="confirmPasswordRules"
                  :type="isConfirmPasswordVisible ? 'text' : 'password'"
                  :append-inner-icon="isConfirmPasswordVisible ? 'ri-eye-off-line' : 'ri-eye-line'"
                  autocomplete="new-password"
                  label="Confirm New Password"
                  placeholder="············"
                  @click:append-inner="isConfirmPasswordVisible = !isConfirmPasswordVisible"
                />
              </VCol>
            </VRow>

            <!-- 👉 Generate Password Button -->
            <VRow>
              <VCol
                cols="12"
                md="6"
              >
                <VBtn
                  color="primary"
                  variant="outlined"
                  @click="generatePassword"
                >
                  Generate
                </VBtn>
                <div v-if="copyState === 'copied' || copyState === 'error'" class="v-input__details">
                  <div class="v-messages">
                    <div class="v-messages__message">
                      {{ copyState === 'copied' ? 'Copied to clipboard' : 'Copy failed' }}
                    </div>
                  </div>
                </div>
              </VCol>
            </VRow>
          </VCardText>

          <!-- 👉 Password Requirements -->
          <VCardText>
            <p class="text-base font-weight-medium mt-2">
              Password Requirements:
            </p>

            <ul class="d-flex flex-column gap-y-3">
              <li
                v-for="item in passwordRequirements"
                :key="item"
                class="d-flex"
              >
                <div>
                  <VIcon
                    size="7"
                    icon="ri-checkbox-blank-circle-fill"
                    class="me-3"
                  />
                </div>
                <span class="font-weight-medium">{{ item }}</span>
              </li>
            </ul>
          </VCardText>

          <!-- 👉 Action Buttons -->
          <VCardText class="d-flex flex-wrap gap-4">
            <VBtn
              type="submit"
              :loading="isSubmitting"
              :disabled="isSubmitting"
            >
              Save changes
            </VBtn>

            <VBtn
              type="button"
              color="secondary"
              variant="outlined"
              :disabled="isSubmitting"
              @click="resetPasswordForm"
            >
              Reset
            </VBtn>
          </VCardText>
        </VForm>
      </VCard>
    </VCol>
    <!-- !SECTION -->

    <!-- SECTION Two-steps verification -->
    <VCol cols="12">
      <VCard title="Two-steps verification">
        <VCardText>
          <p class="font-weight-semibold">
            {{ isTwoFactorEnabled ? 'Two factor authentication is enabled.' : 'Two factor authentication is not enabled yet.' }}
          </p>
          <p>
            Two-factor authentication adds an additional layer of security to your account by requiring more than just a password to log in.
            {{ totpDevices.length === 0 ? 'Create at least one TOTP device below to enable two-factor authentication.' : '' }}
          </p>

          <VAlert
            v-if="totpDevices.length === 0"
            type="info"
            variant="tonal"
            class="mb-4"
          >
            You need to create and verify at least one TOTP device before enabling two-factor authentication.
          </VAlert>

          <p v-if="isTwoFactorEnabled" class="text-body-2 mb-4">
            Active devices: {{ totpDevices.filter(d => d.verified_at).length }} of {{ totpDevices.length }}
          </p>
        </VCardText>
      </VCard>
    </VCol>
    <!-- !SECTION -->

    <VCol cols="12">
      <!-- SECTION: TOTP Devices -->
      <VCard>
        <VCardItem>
          <VCardTitle>TOTP Devices</VCardTitle>
          <template #append>
            <VBtn
              color="primary"
              prepend-icon="ri-add-line"
              @click="openCreateDeviceDialog"
            >
              Create device
            </VBtn>
          </template>
        </VCardItem>

        <VCardText>
          Manage your authenticator apps and TOTP devices used for two-factor authentication.
        </VCardText>

        <VCardText v-if="totpDevices.some(d => !d.verified_at)">
          <VAlert
            type="warning"
            variant="tonal"
            density="compact"
          >
            <span class="text-body-2">Unverified devices will be automatically deleted after 15 minutes. Please verify your device promptly.</span>
          </VAlert>
        </VCardText>

        <!-- 👉 Server Status -->
        <VCardText class="d-flex flex-column gap-y-4">
          <div
            v-for="device in totpDevices"
            :key="device.id"
            class="bg-var-theme-background pa-4"
          >
            <div class="d-flex align-center flex-wrap mb-2">
              <h6 class="text-h6 mb-0 me-3">
                {{ device.name }}
              </h6>
              <VChip
                v-if="device.verified_at"
                size="small"
                color="success"
                variant="tonal"
              >
                Verified
              </VChip>
              <VChip
                v-else
                size="small"
                color="warning"
                variant="tonal"
              >
                Unverified (expires in 15 min)
              </VChip>
            </div>
            <p class="text-sm">
              <span>Created: {{ formatDate(device.created_at) }}</span>
            </p>
            <p v-if="device.verified_at" class="text-sm">
              <span>Verified: {{ formatDate(device.verified_at) }}</span>
            </p>
            <p class="text-sm">
              <span>Last used: {{ formatDate(device.last_used_at) }}</span>
            </p>
            <div class="d-flex justify-end mt-3">
              <VBtn
                size="small"
                color="error"
                variant="outlined"
                prepend-icon="ri-delete-bin-line"
                @click="requestDeleteDevice(device)"
              >
                Delete
              </VBtn>
            </div>
          </div>
        </VCardText>
      </VCard>
      <!-- !SECTION -->
    </VCol>

    <VDialog
      v-model="isCreateDeviceDialogOpen"
      max-width="560"
    >
      <VCard>
        <VCardTitle>{{ newDeviceId ? 'Verify TOTP Device' : 'Create TOTP Device' }}</VCardTitle>
        <VCardText>
          <VForm @submit.prevent="createDevice">
            <!-- Step 1: Device name input -->
            <VTextField
              v-if="!newDeviceId"
              v-model="newDeviceName"
              label="Device name *"
              placeholder="e.g. iPhone 15 Pro, Google Authenticator"
              :rules="[requiredDeviceNameRule]"
              required
              class="mb-4"
            />

            <!-- Step 2: QR code and verification -->
            <div v-if="newDeviceId">
              <p class="text-body-1 mb-4">
                Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.):
              </p>

              <div class="d-flex flex-column align-center gap-4 mb-4">
                <!-- QR Code -->
                <div v-if="qrCodeDataUrl" class="d-flex flex-column align-center">
                  <img
                    :src="qrCodeDataUrl"
                    alt="TOTP QR Code"
                    style="max-width: 256px; width: 100%; height: auto;"
                  />
                </div>

                <div class="w-100">
                  <p class="text-body-2 mb-2">
                    Or enter this secret manually in your authenticator app:
                  </p>
                  <VTextField
                    :model-value="newDeviceSecret"
                    readonly
                    density="compact"
                    variant="outlined"
                  />
                </div>
              </div>

              <VTextField
                v-model="accessCode"
                label="Verification code *"
                placeholder="Enter the 6-digit code from your app"
                :rules="[requiredAccessCodeRule]"
                required
                inputmode="numeric"
                maxlength="6"
              />
            </div>
          </VForm>
        </VCardText>
        <VCardActions class="justify-end">
          <VBtn
            variant="text"
            @click="closeCreateDeviceDialog"
          >
            Cancel
          </VBtn>
          <VBtn
            v-if="!newDeviceId"
            color="primary"
            :disabled="!newDeviceName.trim()"
            @click="createDevice"
          >
            Generate QR Code
          </VBtn>
          <VBtn
            v-else
            color="primary"
            :disabled="!accessCode.trim()"
            @click="createDevice"
          >
            Verify and Save
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- SECTION Recent Devices -->
    <VCol cols="12">
      <!-- 👉 Table -->
      <VCard title="Recent Devices">
        <VDataTable
          :headers="recentDevicesHeaders"
          :items="recentDevices"
          hide-default-footer
          class="text-no-wrap"
        >
          <template #item.browser="{ item }">
            <div class="d-flex">
              <VIcon
                start
                :icon="item.deviceIcon.icon"
                :color="item.deviceIcon.color"
              />
              <span>
                {{ item.browser }}
              </span>
            </div>
          </template>
          <!-- TODO Refactor this after vuetify provides proper solution for removing default footer -->
          <template #bottom />
        </VDataTable>
      </VCard>
    </VCol>
    <!-- !SECTION -->
  </VRow>

  <!-- Dialogs outside VRow -->
  <ConfirmDialog
    v-model="isConfirmDeleteOpen"
    title="Delete TOTP device?"
    :message="devicePendingDelete ? `This will remove ${devicePendingDelete.name} from your account.` : 'This action cannot be undone.'"
    confirm-text="Delete"
    confirm-color="error"
    confirm-variant="outlined"
    @confirm="confirmDeleteDevice"
    @cancel="devicePendingDelete = null"
  />
</template>
