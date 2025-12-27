<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  loading?: boolean
  saving?: boolean
}

interface Settings {
  sessionTimeout: number
  domainUrl: string
  allowRegistration: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  saving: false,
})

const emit = defineEmits<{
  (e: 'save', settings: Settings): void
  (e: 'reset'): void
}>()

const settings = ref<Settings>({
  sessionTimeout: 60,
  domainUrl: 'https://dockspace.io',
  allowRegistration: false,
})

const requiredRule = (value: string | number) => {
  if (typeof value === 'number')
    return Number.isFinite(value) ? true : 'This field is required'
  return value?.trim().length ? true : 'This field is required'
}

const integerRule = (value: number) => {
  return Number.isInteger(value) && value > 0 ? true : 'Enter a whole number'
}

const isValid = computed(() => {
  return Number.isInteger(settings.value.sessionTimeout)
    && settings.value.sessionTimeout > 0
    && settings.value.domainUrl.trim().length > 0
})

const updateSettings = (newSettings: Settings) => {
  settings.value = { ...newSettings }
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
})
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle>Application settings</VCardTitle>
      <VCardSubtitle>Configuration defaults</VCardSubtitle>
    </VCardItem>
    <VCardText>
      <VRow>
        <VCol cols="12">
          <VTextField
            v-model.number="settings.sessionTimeout"
            label="Session timeout (minutes) *"
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
            v-model="settings.domainUrl"
            label="Domain URL *"
            :rules="[requiredRule]"
            :disabled="loading || saving"
            required
          />
        </VCol>
        <VCol cols="12">
          <VSwitch
            v-model="settings.allowRegistration"
            label="Allow self-service registration"
            :disabled="loading || saving"
            color="primary"
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
