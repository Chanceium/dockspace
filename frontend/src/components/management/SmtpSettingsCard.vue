<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  loading?: boolean
  saving?: boolean
}

interface SmtpSettings {
  smtpHost: string
  smtpPort: number
  smtpUsername: string
  smtpPassword: string
  smtpSecurity: string
  smtpFromEmail: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  saving: false,
})

const emit = defineEmits<{
  (e: 'save', settings: SmtpSettings): void
  (e: 'reset'): void
}>()

const settings = ref<SmtpSettings>({
  smtpHost: 'smtp.dockspace.io',
  smtpPort: 587,
  smtpUsername: '',
  smtpPassword: '',
  smtpSecurity: 'starttls',
  smtpFromEmail: 'noreply@dockspace.io',
})

const requiredRule = (value: string | number) => {
  if (typeof value === 'number')
    return Number.isFinite(value) ? true : 'This field is required'
  return value?.trim().length ? true : 'This field is required'
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const isValidEmail = (value: string) => emailPattern.test(value.trim())

const emailRule = (value: string) => {
  if (!value?.trim())
    return 'This field is required'
  return isValidEmail(value) ? true : 'Enter a valid email'
}

const hostRule = (value: string) => {
  if (!value?.trim())
    return 'This field is required'
  return /^[a-zA-Z0-9.-]+$/.test(value.trim()) ? true : 'Enter a valid hostname'
}

const integerRule = (value: number) => {
  return Number.isInteger(value) && value > 0 ? true : 'Enter a whole number'
}

const isValid = computed(() => {
  return !settings.value.smtpHost || hostRule(settings.value.smtpHost) === true
    && integerRule(settings.value.smtpPort) === true
    && settings.value.smtpSecurity.trim().length > 0
    && emailRule(settings.value.smtpFromEmail) === true
})

const updateSettings = (newSettings: SmtpSettings) => {
  settings.value = { ...newSettings }
}

const clearPassword = () => {
  settings.value.smtpPassword = ''
}

const handleSave = () => {
  if (isValid.value) {
    emit('save', settings.value)
  }
}

const handleReset = () => {
  emit('reset')
}

defineExpose({
  updateSettings,
  clearPassword,
})
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle>SMTP outbound mail</VCardTitle>
      <VCardSubtitle>Configure outbound email for password resets and notifications.</VCardSubtitle>
    </VCardItem>
    <VCardText>
      <VRow>
        <VCol cols="12">
          <VTextField
            v-model="settings.smtpHost"
            label="SMTP Host *"
            hint="SMTP server hostname for outbound email."
            persistent-hint
            :rules="[hostRule]"
            :disabled="loading || saving"
            :error="false"
            required
          />
        </VCol>
        <VCol cols="12">
          <VTextField
            v-model.number="settings.smtpPort"
            label="SMTP Port *"
            hint="SMTP port (e.g., 587 for STARTTLS, 465 for SSL)."
            persistent-hint
            type="number"
            min="1"
            step="1"
            :rules="[integerRule]"
            :disabled="loading || saving"
            required
          />
        </VCol>
        <VCol cols="12">
          <VTextField
            v-model="settings.smtpUsername"
            label="SMTP Username *"
            hint="SMTP username for authentication."
            persistent-hint
            :rules="[requiredRule]"
            :disabled="loading || saving"
            required
          />
        </VCol>
        <VCol cols="12">
          <VTextField
            v-model="settings.smtpPassword"
            label="SMTP Password *"
            hint="SMTP password for authentication."
            persistent-hint
            type="password"
            :disabled="loading || saving"
            required
          />
        </VCol>
        <VCol cols="12">
          <VSelect
            v-model="settings.smtpSecurity"
            label="SMTP Security *"
            hint="Choose encryption for SMTP."
            persistent-hint
            :items="[
              { title: 'None', value: 'none' },
              { title: 'STARTTLS', value: 'starttls' },
              { title: 'SSL/TLS', value: 'ssl' },
            ]"
            :rules="[requiredRule]"
            :disabled="loading || saving"
            required
          />
        </VCol>
        <VCol cols="12">
          <VTextField
            v-model="settings.smtpFromEmail"
            label="From Email *"
            hint="Address used as the From header for outbound email."
            persistent-hint
            :rules="[emailRule]"
            :disabled="loading || saving"
            required
          />
        </VCol>
      </VRow>
    </VCardText>
    <VCardActions class="d-flex flex-wrap gap-4 justify-end">
      <VBtn
        color="primary"
        variant="flat"
        :disabled="!isValid || loading || saving"
        :loading="saving"
        @click="handleSave"
      >
        Save changes
      </VBtn>
      <VBtn
        color="secondary"
        variant="outlined"
        :disabled="loading || saving"
        @click="handleReset"
      >
        Reset
      </VBtn>
    </VCardActions>
  </VCard>
</template>
